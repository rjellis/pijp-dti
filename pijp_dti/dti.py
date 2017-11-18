import csv
import gzip
import os
import shutil
import subprocess

import nibabel as nib
import numpy as np
from dipy.io import read_bvals_bvecs
from pijp.core import Step, get_project_dir
from pijp.repositories import DicomRepository

from pijp_dti import dtfunc


def get_process_dir(project):
    return os.path.join(get_project_dir(project), 'dti')


def get_subjects_dir(project):
    sdir = os.path.join(get_process_dir(project), 'subjects')
    if not os.path.isdir(sdir):
        os.makedirs(sdir)
    return sdir


def get_case_dir(project, code):
    return os.path.join(get_subjects_dir(project), code)


class DTStep(Step):
    def __init__(self, project, code, args):
        super(DTStep, self).__init__(project, code, args)
        self.subjects_dir = get_subjects_dir(project)
        self.working_dir = get_case_dir(project, code)
        self.logdir = os.path.join(get_process_dir(project), 'logs', code)

        self.fdwi = os.path.join(self.working_dir, 'stage', self.code + '.nii.gz')
        self.fbval = os.path.join(self.working_dir, 'stage', self.code + '.bval')
        self.fbvec = os.path.join(self.working_dir, 'stage', self.code + '.bvec')

        self.prereg = os.path.join(self.working_dir, 'prereg', self.code + '_prereg.nii.gz')

        self.reg = os.path.join(self.working_dir, 'reg', self.code + '_reg.nii.gz')
        self.fbvec_reg = os.path.join(self.working_dir, 'reg', self.code + '_bvec_reg.npy')

        self.fa = os.path.join(self.working_dir, 'tenfit', self.code + '_fa.nii.gz')
        self.md = os.path.join(self.working_dir, 'tenfit', self.code + '_md.nii.gz')
        self.ga = os.path.join(self.working_dir, 'tenfit', self.code + '_ga.nii.gz')
        self.ad = os.path.join(self.working_dir, 'tenfit', self.code + '_ad.nii.gz')
        self.rd = os.path.join(self.working_dir, 'tenfit', self.code + '_rd.nii.gz')
        self.evals = os.path.join(self.working_dir, 'tenfit', self.code + '_evals.npy')
        self.evecs = os.path.join(self.working_dir, 'tenfit', self.code + '_evecs.npy')
        self.warped_fa = os.path.join(self.working_dir, 'tenfit', self.code + '_warped_fa.nii.gz')
        self.warped_labels = os.path.join(self.working_dir, 'tenfit', self.code + '_warped_labels.nii.gz')

        self.fa_roi = os.path.join(self.working_dir, 'roistats', self.code + '_fa_roi.csv')
        self.md_roi = os.path.join(self.working_dir, 'roistats', self.code + '_md_roi.csv')
        self.ga_roi = os.path.join(self.working_dir, 'roistats', self.code + '_ga_roi.csv')
        self.ad_roi = os.path.join(self.working_dir, 'roistats', self.code + '_ad_roi.csv')
        self.rd_roi = os.path.join(self.working_dir, 'roistats', self.code + '_rd_roi.csv')

        fpath = os.path.dirname(__file__)
        self.template = fpath + '/templates/fa_template.nii'
        self.template_labels = fpath + '/templates/fa_labels.nii'
        self.labels = fpath + '/templates/labels.npy'

    def _load_nii(self, fname):
        self.logger.debug('Loading image: {}'.format(fname))
        img = nib.load(fname)
        dat = img.get_data()
        aff = img.affine
        return dat, aff

    def _load_bval_bvec(self, fbval, fbvec):
        self.logger.debug('Loading bvals and bvecs: {} {}'.format(fbval, fbvec))
        bval, bvec = read_bvals_bvecs(fbval, fbvec)
        return bval, bvec

    def _save_nii(self, dat, aff, fname):
        img = nib.Nifti1Image(dat, aff)
        nib.nifti1.save(img, fname.rstrip('.gz'))
        with open(fname.rstrip('.gz'), 'rb') as f_in:
            with gzip.open(fname, 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)
        os.remove(fname.rstrip('.gz'))
        self.logger.info('Saving image: {}'.format(fname))

    def _run_cmd(self, cmd):
        self.logger.debug(cmd)
        args = cmd.split()
        p = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        (output, error) = p.communicate()
        if output:
            self.logger.info(output)
        if error:
            self.logger.error(error)


class Stage(DTStep):
    process_name = "DTI"
    step_name = "Stage"
    step_cli = "stage"

    def __init__(self, project, code, args):
        super(Stage, self).__init__(project, code, args)
        self.next_step = Preregister

    def run(self):
        self.logger.debug('Building directories in {}'.format(self.working_dir))

        stage_dir = os.path.join(self.working_dir, 'stage')
        if not os.path.isdir(stage_dir):
            os.makedirs(stage_dir)
        prereg_dir = os.path.join(self.working_dir, 'prereg')
        if not os.path.isdir(prereg_dir):
            os.makedirs(prereg_dir)
        reg_dir = os.path.join(self.working_dir, 'reg')
        if not os.path.isdir(reg_dir):
            os.makedirs(reg_dir)
        tenfit_dir = os.path.join(self.working_dir, 'tenfit')
        if not os.path.isdir(tenfit_dir):
            os.makedirs(tenfit_dir)
        roiavg_dir = os.path.join(self.working_dir, 'roistats')
        if not os.path.isdir(roiavg_dir):
            os.makedirs(roiavg_dir)

        DicomRepository.fetch_dicoms(self.code, stage_dir)
        cmd = 'dcm2nii {}'.format(stage_dir)
        self.logger.debug(cmd)
        self._run_cmd(cmd)

        pref = stage_dir + '/'
        with os.scandir(stage_dir) as it:
            for entry in it:
                if entry.name.split('.')[-1] == 'gz':
                    os.rename(pref + entry.name, pref + self.code + '.nii.gz')
                if entry.name.split('.')[-1] == 'bval':
                    os.rename(pref + entry.name, pref + self.code + '.bval')
                if entry.name.split('.')[-1] == 'bvec':
                    os.rename(pref + entry.name, pref + self.code + '.bvec')
                else:
                    os.remove(entry.name)


class Preregister(DTStep):
    process_name = "DTI"
    step_name = "Preregister"
    step_cli = "prereg"

    prev_step = [Stage]

    def __init__(self, project, code, args):
        super(Preregister, self).__init__(project, code, args)
        self.next_step = Register

    def run(self):
        dat, aff = self._load_nii(self.fdwi)
        bval, bvec = self._load_bval_bvec(self.fbval, self.fbvec)
        self.logger.debug('Denoising and Masking the image')
        denoised = dtfunc.denoise_pca(dat, bval, bvec)
        masked = dtfunc.mask(denoised)
        self._save_nii(masked, aff, self.prereg)


class Register(DTStep):
    process_name = "DTI"
    step_name = "Register"
    step_cli = "reg"

    prev_step = [Preregister]

    def __init__(self, project, code, args):
        super(Register, self).__init__(project, code, args)
        self.next_step = TensorFit

    def run(self):
        dat, aff = self._load_nii(self.prereg)
        bval, bvec = self._load_bval_bvec(self.fbval, self.fbvec)
        b0 = dtfunc.b0_avg(dat, aff, bval)
        self.logger.debug('Registering the image to its averaged b0 image')
        reg_dat, bvec = dtfunc.register(b0, dat, aff, aff, bval, bvec)
        self._save_nii(reg_dat, aff, self.reg)
        np.save(self.fbvec_reg, bvec)


class TensorFit(DTStep):
    process_name = "DTI"
    step_name = "TensorFit"
    step_cli = "tenfit"

    prev_step = [Register]

    def __init__(self, project, code, args):
        super(TensorFit, self).__init__(project, code, args)

    def run(self):
        dat, aff = self._load_nii(self.reg)
        template, template_aff = self._load_nii(self.template)
        temp_labels, temp_labels_aff = self._load_nii(self.template_labels)
        bval, bvec = self._load_bval_bvec(self.fbval, self.fbvec)
        bvec = np.load(self.fbvec_reg)

        self.logger.debug('Fitting the tensor')
        evals, evecs, tenfit = dtfunc.fit_dti(dat, bval, bvec)
        fa = tenfit.fa
        md = tenfit.md
        ga = tenfit.ga  # this is geodesic anisotropy, not general
        ad = tenfit.ad
        rd = tenfit.rd

        self.logger.debug('Building nonlinear registration map for FA')
        warped_template, mapping = dtfunc.symm_diff_registration(
            fa, template,
            aff, template_aff)

        warped_labels = mapping.transform(temp_labels, interpolation='nearest')
        warped_fa = mapping.transform_inverse(fa)

        self._save_nii(fa, aff, self.fa)
        self._save_nii(md, aff, self.md)
        self._save_nii(ga, aff, self.ga)
        self._save_nii(ad, aff, self.ad)
        self._save_nii(rd, aff, self.rd)
        self._save_nii(warped_fa, template_aff, self.warped_fa)
        self._save_nii(warped_labels, aff, self.warped_labels)
        np.save(self.evals, evals)
        np.save(self.evecs, evecs)


class RoiStats(DTStep):
    process_name = "DTI"
    step_name = "RoiStats"
    step_cli = "roistats"

    prev_step = [TensorFit]

    def __init__(self, project, code, args):
        super(RoiStats, self).__init__(project, code, args)

    def run(self):
        fa, aff = self._load_nii(self.fa)
        md, aff = self._load_nii(self.md)
        ga, aff = self._load_nii(self.ga)
        ad, aff = self._load_nii(self.ad)
        rd, aff = self._load_nii(self.rd)
        warped_labels, aff = self._load_nii(self.warped_labels)
        labels = np.load(self.labels).item()

        fa_roi = dtfunc.roi_stats(fa, warped_labels, labels)
        md_roi = dtfunc.roi_stats(md, warped_labels, labels)
        ga_roi = dtfunc.roi_stats(ga, warped_labels, labels)
        ad_roi = dtfunc.roi_stats(ad, warped_labels, labels)
        rd_roi = dtfunc.roi_stats(rd, warped_labels, labels)

        self._save_dict(fa_roi, self.fa_roi)
        self._save_dict(md_roi, self.md_roi)
        self._save_dict(ga_roi, self.ga_roi)
        self._save_dict(ad_roi, self.ad_roi)
        self._save_dict(rd_roi, self.rd_roi)

    def _save_dict(self, dictionary, csv_path):
        with open(csv_path, 'w') as csv_file:
            writer = csv.writer(csv_file)
            for key, value in dictionary.items():
                writer.writerow([key, value])
        self.logger.debug("Saving dictionary {}".format(csv_path))


class StoreInDatabase(DTStep):
    process_name = "DTI"
    step_name = "StoreInDatabase"
    step_cli = "db"

    def __init__(self, project, code, args):
        super(StoreInDatabase, self).__init__(project, code, args)

    def run(self):
        # TODO store CSV's to database
        pass
