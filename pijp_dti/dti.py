import csv
import gzip
import os
import tempfile
import shutil
import subprocess
import datetime
import getpass
import logging
import random

import nibabel as nib
import numpy as np
from dipy.io import read_bvals_bvecs
from pijp import util
from pijp.core import Step, get_project_dir
from pijp.repositories import DicomRepository, ProcessingLog
from pijp.exceptions import ProcessingError, NoLogProcessingError
from pijp.engine import run_module, run_file

from pijp_dti import dtfunc
from pijp_dti import dtiQC, QCinter
from pijp_dti.repository import DTIRepository

LOGGER = logging.getLogger(__name__)
PROCESS_TITLE = 'dti'
VERSION = "0.1.0"


def get_process_dir(project):
    return os.path.join(get_project_dir(project), 'dti')


def get_case_dir(project, code):
    cdir = os.path.join(get_process_dir(project), code)
    if not os.path.isdir(cdir):
        os.makedirs(cdir)
    return cdir


def get_dcm2niix_home():
    dcm2niix = util.configuration['dcm2niix']
    if not os.path.exists(dcm2niix):
        raise Exception("dcm2niix home not found: %s" % dcm2niix)
    return dcm2niix


class DTIStep(Step):

    def __init__(self, project, code, args):
        super(DTIStep, self).__init__(project, code, args)

        self.working_dir = get_case_dir(project, code)
        self.logdir = os.path.join(get_process_dir(project), 'logs', code)

        self.fdwi = os.path.join(self.working_dir, 'stage', self.code + '.nii.gz')
        self.fbval = os.path.join(self.working_dir, 'stage', self.code + '.bval')
        self.fbvec = os.path.join(self.working_dir, 'stage', self.code + '.bvec')
        self.denoised = os.path.join(self.working_dir, 'prereg', self.code + '_denoised.nii.gz')
        self.auto_mask = os.path.join(self.working_dir, 'prereg', self.code + '_auto_mask.nii.gz')
        self.reg = os.path.join(self.working_dir, 'reg', self.code + '_reg.nii.gz')
        self.fbvec_reg = os.path.join(self.working_dir, 'reg', self.code + '_bvec_reg.npy')
        self.fa = os.path.join(self.working_dir, 'tenfit', self.code + '_fa.nii.gz')
        self.md = os.path.join(self.working_dir, 'tenfit', self.code + '_md.nii.gz')
        self.ga = os.path.join(self.working_dir, 'tenfit', self.code + '_ga.nii.gz')
        self.ad = os.path.join(self.working_dir, 'tenfit', self.code + '_ad.nii.gz')
        self.rd = os.path.join(self.working_dir, 'tenfit', self.code + '_rd.nii.gz')
        self.evals = os.path.join(self.working_dir, 'tenfit', self.code + '_evals.nii.gz')
        self.evecs = os.path.join(self.working_dir, 'tenfit', self.code + '_evecs.nii.gz')
        self.warp_map = os.path.join(self.working_dir, 'tenfit', self.code + '_warp_map.npy')
        self.inverse_warp_map = os.path.join(self.working_dir, 'tenfit', self.code + '_inverse_warp_map.npy')
        self.warped_fa = os.path.join(self.working_dir, 'tenfit', self.code + '_inverse_warped_fa.nii.gz')
        self.warped_labels = os.path.join(self.working_dir, 'tenfit', self.code + '_warped_labels.nii.gz')
        self.fa_roi = os.path.join(self.working_dir, 'roistats', self.code + '_fa_roi.csv')
        self.md_roi = os.path.join(self.working_dir, 'roistats', self.code + '_md_roi.csv')
        self.ga_roi = os.path.join(self.working_dir, 'roistats', self.code + '_ga_roi.csv')
        self.ad_roi = os.path.join(self.working_dir, 'roistats', self.code + '_ad_roi.csv')
        self.rd_roi = os.path.join(self.working_dir, 'roistats', self.code + '_rd_roi.csv')
        self.final_mask = os.path.join(self.working_dir, 'qc', self.code + '_final_mask.nii.gz')
        self.mask_mosaic = os.path.join(self.working_dir, 'qc', self.code + '_mask_mosaic.png')
        self.warp_mosaic = os.path.join(self.working_dir, 'qc', self.code + '_warp_mosaic.png')
        self.review_flag = os.path.join(self.working_dir, "qc.inprocess")

        fpath = os.path.dirname(__file__)
        self.template = os.path.join(fpath, 'templates', 'fa_template.nii')
        self.template_labels = os.path.join(fpath, 'templates', 'fa_labels.nii')
        self.labels = os.path.join(fpath, 'templates', 'labels.npy')
        self.mask_fig = None
        self.warp_fig = None

    def _load_nii(self, fname):
        self.logger.info('loading {}'.format(fname))
        img = nib.load(fname)
        dat = img.get_data()
        aff = img.affine
        return dat, aff

    def _load_bval_bvec(self, fbval, fbvec):
        self.logger.info('loading {} {}'.format(fbval, fbvec))
        bval, bvec = read_bvals_bvecs(fbval, fbvec)
        return bval, bvec

    def _save_nii(self, dat, aff, fname):
        img = nib.Nifti1Image(dat, aff)
        nii = fname.rstrip('.gz')
        nib.nifti1.save(img, nii)
        with open(nii, 'rb') as f_in:
            with gzip.open(fname, 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)
        os.remove(nii)
        self.logger.info('saving {}'.format(fname))

    def _run_cmd(self, cmd):
        self.logger.debug(cmd)
        args = cmd.split()
        p = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        (output, error) = p.communicate()
        if output:
            self.logger.info(output.decode('utf-8'))
        if error:
            self.logger.error(error.decode('utf-8'))


class Stage(DTIStep):
    process_name = "DTI"
    step_name = "Stage"
    step_cli = "stage"

    prev_step = None

    def __init__(self, project, code, args):
        super(Stage, self).__init__(project, code, args)
        self.next_step = Preregister

    def run(self):

        stage_dir = os.path.join(self.working_dir, 'stage')
        prereg_dir = os.path.join(self.working_dir, 'prereg')
        reg_dir = os.path.join(self.working_dir, 'reg')
        tenfit_dir = os.path.join(self.working_dir, 'tenfit')
        roiavg_dir = os.path.join(self.working_dir, 'roistats')
        qc_dir = os.path.join(self.working_dir, 'qc')

        dirs = [stage_dir, prereg_dir, reg_dir, tenfit_dir, roiavg_dir, qc_dir]
        for dr in dirs:
            if not os.path.isdir(dr):
                os.makedirs(dr)
            self.logger.info('building directory {}'.format(dr))

        source = DicomRepository().get_series_files(self.code)

        if source is None:
            raise ProcessingError("Could not find staging data.")

        dcm_dir = self._copy_files(source)
        cmd = 'dcm2niix -z i -m y -o {} {}'.format(stage_dir, dcm_dir)
        self._run_cmd(cmd)

        with os.scandir(stage_dir) as it:
            for entry in it:
                if entry.name.endswith('.nii.gz'):
                    os.rename(entry.path, os.path.join(stage_dir, self.code + '.nii.gz'))
                elif entry.name.endswith('.bval'):
                    os.rename(entry.path, os.path.join(stage_dir, self.code + '.bval'))
                elif entry.name.endswith('.bvec'):
                    os.rename(entry.path, os.path.join(stage_dir, self.code + '.bvec'))
                else:
                    os.remove(entry.path)

    def _copy_files(self, source):
        tmp = tempfile.mkdtemp()
        self.logger.debug("Copying %s files..." % (len(source)))

        for src in source:
            dst = os.path.join(tmp, os.path.basename(src))
            self.logger.debug("Copying file: %s -> %s" % (src, dst))
            shutil.copyfile(src, dst)
            if not os.path.exists(dst):
                raise Exception("Failed to copy file: %s" % dst)

        return os.path.join(tmp, os.path.basename(source[0]))

    @classmethod
    def get_queue(cls, project_name):
        plog = ProcessingLog()
        attempted = plog.get_step_attempted(project_name, cls.process_name, cls.step_name)
        attempted_codes = [row['Code'] for row in attempted]
        dtis = DTIRepository().get_project_dtis(project_name)
        todo = [{'ProjectName': project_name, "Code": row['Code']} for row in dtis if row['Code'] not in
                attempted_codes]
        return todo


class Preregister(DTIStep):
    process_name = "DTI"
    step_name = "Preregister"
    step_cli = "prereg"

    prev_step = [Stage]

    def __init__(self, project, code, args):
        super(Preregister, self).__init__(project, code, args)
        self.next_step = MaskQC

    def run(self):
        dat, aff = self._load_nii(self.fdwi)
        self.logger.info('denoising and masking the image')
        denoised = dtfunc.denoise(dat)
        mask = dtfunc.mask(denoised)
        self._save_nii(denoised, aff, self.denoised)
        self._save_nii(mask, aff, self.auto_mask)
        dtiQC.get_mask_mosaic(self.denoised, self.auto_mask, self.mask_mosaic)


class MaskQC(DTIStep):
    process_name = "DTI"
    step_name = "MaskQC"
    step_cli = "qc"
    interactive = True
    prev_step = [Preregister]

    def __init__(self, project, code, args):
        super(MaskQC, self).__init__(project, code, args)
        self.next_step = None

    def under_review(self):
        if os.path.exists(self.review_flag):
            self._print_review_info()
            return True
        return False

    def _print_review_info(self):
        flag = open(self.review_flag, 'r')
        lines = flag.readlines()
        flag.close()
        self.logger.info('%s is under review by %s starting %s' % (self.code, lines[0].rstrip('\n'), lines[1]))

    def initiate(self):
        if self.under_review():
            raise NoLogProcessingError("This case is currently being reviewed.")
        flag = open(self.review_flag, 'w')
        flag.write(getpass.getuser() + '\n' + datetime.datetime.now().strftime('%c'))
        flag.close()

    def run(self):

        mask_fig = dtiQC.get_mask_mosaic(self.denoised, self.auto_mask, self.mask_mosaic)

        try:
            (result, comments) = QCinter.qc_tool(mask_fig, self.code)
            self.outcome = result
            self.comments = comments
            if result == 'pass':
                shutil.copyfile(self.auto_mask, self.final_mask)
                self.next_step = Register
            if result == 'fail':
                shutil.copyfile(self.auto_mask, self.final_mask)
                self.next_step = Register
        finally:
            os.remove(self.review_flag)

    @classmethod
    def get_next(cls, project_name, args):
        cases = DTIRepository().get_mask_qc_list(project_name)
        LOGGER.info("%s cases in queue." % len(cases))

        cases = [x["Code"] for x in cases]
        while len(cases) != 0:
            code = random.choice(cases)
            cases.remove(code)
            next_job = MaskQC(project_name, code, args)
            if not next_job.under_review():
                return next_job


class Register(DTIStep):
    process_name = "DTI"
    step_name = "Register"
    step_cli = "reg"

    prev_step = [MaskQC]

    def __init__(self, project, code, args):
        super(Register, self).__init__(project, code, args)
        self.next_step = TensorFit

    def run(self):
        dat, aff = self._load_nii(self.denoised)
        mask, mask_aff = self._load_nii(self.final_mask)
        bval, bvec = self._load_bval_bvec(self.fbval, self.fbvec)
        b0 = dtfunc.b0_avg(dat, aff, bval)
        self.logger.info('registering the image to its averaged b0 image')
        reg_dat, bvec = dtfunc.register(b0, dat, aff, aff, bval, bvec)
        bin_mask = mask
        bin_mask[mask > 0] = 1
        bin_mask[bin_mask < 1] = 0
        reg_dat = dtfunc.apply_mask(reg_dat, mask)

        self._save_nii(reg_dat, aff, self.reg)
        np.save(self.fbvec_reg, bvec)


class TensorFit(DTIStep):
    process_name = "DTI"
    step_name = "TensorFit"
    step_cli = "tenfit"

    prev_step = [Register]

    def __init__(self, project, code, args):
        super(TensorFit, self).__init__(project, code, args)
        self.next_step = WarpQC

    def run(self):
        dat, aff = self._load_nii(self.reg)
        template, template_aff = self._load_nii(self.template)
        temp_labels, temp_labels_aff = self._load_nii(self.template_labels)
        bval, bvec = self._load_bval_bvec(self.fbval, self.fbvec)
        bvec = np.load(self.fbvec_reg)

        self.logger.info('fitting the tensor')
        evals, evecs, tenfit = dtfunc.fit_dti(dat, bval, bvec)

        self.logger.info('generating nonlinear registration map for FA')
        warped_template, mapping = dtfunc.sym_diff_registration(
            tenfit.fa, template,
            aff, template_aff)

        warped_labels = mapping.transform(temp_labels, interpolation='nearest')
        warped_fa = mapping.transform_inverse(tenfit.fa)
        warp_map = mapping.get_forward_field()
        inverse_warp_map = mapping.get_backward_field()

        self._save_nii(tenfit.fa, aff, self.fa)
        self._save_nii(tenfit.md, aff, self.md)
        self._save_nii(tenfit.ga, aff, self.ga)
        self._save_nii(tenfit.ad, aff, self.ad)
        self._save_nii(tenfit.rd, aff, self.rd)
        self._save_nii(warped_fa, template_aff, self.warped_fa)
        self._save_nii(warped_labels, aff, self.warped_labels)
        self._save_nii(evals, aff, self.evals)
        self._save_nii(evecs, aff, self.evecs)
        np.save(self.warp_map, warp_map)
        np.save(self.inverse_warp_map, inverse_warp_map)


class WarpQC(DTIStep):
    process_name = "DTI"
    step_name = "WarpQC"
    step_cli = "wqc"
    interactive = True
    prev_step = [TensorFit]

    def __init__(self, project, code, args):
        super(WarpQC, self).__init__(project, code, args)
        self.next_step = None

    def under_review(self):
        if os.path.exists(self.review_flag):
            self._print_review_info()
            return True
        return False

    def _print_review_info(self):
        flag = open(self.review_flag, 'r')
        lines = flag.readlines()
        flag.close()
        self.logger.info('%s is under review by %s starting %s' % (self.code, lines[0].rstrip('\n'), lines[1]))

    def initiate(self):
        if self.under_review():
            raise NoLogProcessingError("This case is currently being reviewed.")
        flag = open(self.review_flag, 'w')
        flag.write(getpass.getuser() + '\n' + datetime.datetime.now().strftime('%c'))
        flag.close()

    def run(self):

        mosaic_fig = dtiQC.get_warp_mosaic(self.fa, self.warped_labels, self.warp_mosaic)

        try:
            (result, comments) = QCinter.qc_tool(mosaic_fig, self.code)
            self.outcome = result
            self.comments = comments
            if result == 'pass':
                self.next_step = RoiStats
            if result == 'fail':
                self.next_step = RoiStats
        finally:
            os.remove(self.review_flag)

    @classmethod
    def get_next(cls, project_name, args):
        cases = DTIRepository().get_mask_qc_list(project_name)
        LOGGER.info("%s cases in queue." % len(cases))

        cases = [x["Code"] for x in cases]
        while len(cases) != 0:
            code = random.choice(cases)
            cases.remove(code)
            next_job = MaskQC(project_name, code, args)
            if not next_job.under_review():
                return next_job


class RoiStats(DTIStep):
    process_name = "DTI"
    step_name = "RoiStats"
    step_cli = "stats"

    prev_step = [WarpQC]

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

        self.logger.info('calculating roi statistics')

        measures = {'fa': [fa, self.fa_roi],
                    'md': [md, self.md_roi],
                    'ga': [ga, self.ga_roi],
                    'ad': [ad, self.ad_roi],
                    'rd': [rd, self.rd_roi]}

        for idx in measures.values():
            idx[0][fa < 0.05] = 0
            idx[0][fa > 0.85] = 0
            stats = dtfunc.roi_stats(idx[0], warped_labels, labels)
            self._write_array(stats, idx[1])

    def _write_array(self, array, csv_path):
        with open(csv_path, 'w') as csv_file:
            writer = csv.writer(csv_file)
            for line in array:
                writer.writerow(line)
        self.logger.debug("saving {}".format(csv_path))

def run():
    import sys
    current_module = sys.modules[__name__]
    run_module(current_module)


if __name__ == "__main__":
    run_file(os.path.abspath(__file__))
