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
from pijp_dti import mosaic, QCinter
from pijp_dti.repo import DTIRepository

LOGGER = logging.getLogger(__name__)
PROCESS_TITLE = 'pijp_dti'
VERSION = "0.2.0"


def get_process_dir(project):
    return os.path.join(get_project_dir(project), 'pijp_dti')


def get_case_dir(project, code):
    cdir = os.path.join(get_process_dir(project), code)
    if not os.path.isdir(cdir):
        os.makedirs(cdir)
    return cdir


def get_dcm2niix():
    dcm2niix = util.configuration['dcm2niix']
    if not os.path.exists(dcm2niix):
        raise Exception("dcm2niix not found: %s" % dcm2niix)
    return dcm2niix


def get_mask_editor():
    mask_editor = util.configuration['fslview']
    if not os.path.exists(mask_editor):
        raise Exception("fslview not found")
    return mask_editor


class DTIStep(Step):

    def __init__(self, project, code, args):
        super(DTIStep, self).__init__(project, code, args)

        self.working_dir = get_case_dir(project, code)
        self.logdir = os.path.join(get_process_dir(project), 'logs', code)
        self.stage_dir = os.path.join(self.working_dir, '0Stage')
        self.den_dir = os.path.join(self.working_dir, '1Denoise')
        self.reg_dir = os.path.join(self.working_dir, '2Register')
        self.mask_dir = os.path.join(self.working_dir, '3Mask')
        self.tenfit_dir = os.path.join(self.working_dir, '4Tenfit')
        self.warp_dir = os.path.join(self.working_dir, '5Warp')
        self.seg_dir = os.path.join(self.working_dir, '6Segment')
        self.roiavg_dir = os.path.join(self.working_dir, '7Stats')
        self.qc_dir = os.path.join(self.working_dir, '8QC')
        self.fdwi = os.path.join(self.stage_dir, self.code + '.nii.gz')
        self.fbval = os.path.join(self.stage_dir, self.code + '.bval')
        self.fbvec = os.path.join(self.stage_dir, self.code + '.bvec')
        self.b0 = os.path.join(self.reg_dir, self.code + '_b0.nii.gz')
        self.reg = os.path.join(self.reg_dir, self.code + '_reg.nii.gz')
        self.fbvec_reg = os.path.join(self.reg_dir, self.code + '_bvec_reg.npy')
        self.denoised = os.path.join(self.den_dir, self.code + '_denoised.nii.gz')
        self.auto_mask = os.path.join(self.mask_dir, self.code + '_auto_mask.nii.gz')
        self.masked = os.path.join(self.mask_dir, self.code + '_masked.nii.gz')
        self.fa = os.path.join(self.tenfit_dir, self.code + '_fa.nii.gz')
        self.md = os.path.join(self.tenfit_dir, self.code + '_md.nii.gz')
        self.ga = os.path.join(self.tenfit_dir, self.code + '_ga.nii.gz')
        self.ad = os.path.join(self.tenfit_dir, self.code + '_ad.nii.gz')
        self.rd = os.path.join(self.tenfit_dir, self.code + '_rd.nii.gz')
        self.evals = os.path.join(self.tenfit_dir, self.code + '_evals.nii.gz')
        self.evecs = os.path.join(self.tenfit_dir, self.code + '_evecs.nii.gz')
        self.warp_map = os.path.join(self.warp_dir, self.code + '_warp_map.npy')
        self.inverse_warp_map = os.path.join(self.warp_dir, self.code + '_inverse_warp_map.npy')
        self.warped_fa = os.path.join(self.warp_dir, self.code + '_inverse_warped_fa.nii.gz')
        self.warped_labels = os.path.join(self.warp_dir, self.code + '_warped_labels.nii.gz')
        self.segmented = os.path.join(self.seg_dir, self.code + '_segmented.nii.gz')
        self.fa_roi = os.path.join(self.roiavg_dir, self.code + '_fa_roi.csv')
        self.md_roi = os.path.join(self.roiavg_dir, self.code + '_md_roi.csv')
        self.ga_roi = os.path.join(self.roiavg_dir, self.code + '_ga_roi.csv')
        self.ad_roi = os.path.join(self.roiavg_dir, self.code + '_ad_roi.csv')
        self.rd_roi = os.path.join(self.roiavg_dir, self.code + '_rd_roi.csv')
        self.final_mask = os.path.join(self.qc_dir, self.code + '_final_mask.nii.gz')
        self.mask_mosaic = os.path.join(self.qc_dir, self.code + '_mask_mosaic.png')
        self.warp_mosaic = os.path.join(self.qc_dir, self.code + '_warp.png')
        self.seg_mosaic = os.path.join(self.qc_dir, self.code + '_segment_mosaic.png')
        self.review_flag = os.path.join(self.working_dir, "qc.inprocess")

        fpath = os.path.dirname(__file__)
        self.template = os.path.join(fpath, 'templates', 'fa_template.nii')
        self.template_labels = os.path.join(fpath, 'templates', 'fa_labels.nii')
        self.labels_lookup = os.path.join(fpath, 'templates', 'labels.npy')

    def _load_nii(self, fname):
        self.logger.info('loading {}'.format(fname.split('/')[-1]))
        img = nib.load(fname)
        dat = img.get_data()
        aff = img.affine

        return dat, aff

    def _load_bval_bvec(self, fbval, fbvec):
        self.logger.info('loading {} {}'.format(fbval.split('/')[-1], fbvec.split('/')[-1]))
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
        self.logger.info('saving {}'.format(fname.split('/')[-1]))

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
    """Convert Dicoms and set up the pipeline
    """
    process_name = "pijp dti"
    step_name = "Stage"
    step_cli = "stage"

    def __init__(self, project, code, args):
        super(Stage, self).__init__(project, code, args)
        self.next_step = Denoise

    def run(self):

        source = DicomRepository().get_series_files(self.code)

        if source is None:
            raise ProcessingError("Could not find staging data.")

        try:

            dirs = [self.stage_dir, self.den_dir, self.reg_dir, self.mask_dir, self.tenfit_dir, self.warp_dir,
                    self.seg_dir, self.roiavg_dir, self.qc_dir]
            for dr in dirs:
                if not os.path.isdir(dr):
                    os.makedirs(dr)
                self.logger.info('building directory {}'.format(dr))

            dcm2niix = get_dcm2niix()
            dcm_dir = self._copy_files(source)
            cmd = '{} -z i -m y -o {} -f {} {}'.format(dcm2niix, self.stage_dir, self.code, dcm_dir)
            self._run_cmd(cmd)

            read_bvals_bvecs(self.fbval, self.fbvec)

            if len(nib.load(self.fdwi).get_data().shape) != 4:
                self.outcome = 'Error'
                self.comments = 'DWI must have 4 dimensions'
                self.next_step = None

        except FileNotFoundError as e:
            self.outcome = 'Error'
            self.comments = str(e)
            self.logger.info('failed to find .bval or .bvec')
            self.next_step = None
            shutil.rmtree(get_case_dir(self.project, self.code))

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


class Denoise(DTIStep):
    """Denoise the DWI using Local PCA
    """
    process_name = "pijp dti"
    step_name = "Denoise"
    step_cli = "denoise"

    prev_step = [Stage]

    def __init__(self, project, code, args):
        super(Denoise, self).__init__(project, code, args)
        self.next_step = Register

    def run(self):
        self.logger.info("denoising the DWI")
        dat, aff = self._load_nii(self.fdwi)
        bval, bvec = self._load_bval_bvec(self.fbval, self.fbvec)
        denoised = dtfunc.denoise_pca(dat, bval, bvec)

        self._save_nii(denoised, aff, self.denoised)


class Register(DTIStep):
    """Rigidly register the diffusion weighted directions to an averaged b0 volume
    """
    process_name = "pijp dti"
    step_name = "Register"
    step_cli = "register"
    prev_step = [Denoise]

    def __init__(self, project, code, args):
        super(Register, self).__init__(project, code, args)
        self.next_step = Mask

    def run(self):
        self.logger.info('averaging the b0 volume')
        dat, aff = self._load_nii(self.denoised)
        bval, bvec = self._load_bval_bvec(self.fbval, self.fbvec)
        b0 = dtfunc.b0_avg(dat, aff, bval)
        self.logger.info('registering the DWI to its averaged b0 volume')
        reg_dat, bvec = dtfunc.register(b0, dat, aff, aff, bval, bvec)

        self._save_nii(b0, aff, self.b0)
        self._save_nii(reg_dat, aff, self.reg)
        np.save(self.fbvec_reg, bvec)


class Mask(DTIStep):
    """Skull strip the average b0 volume
    """
    process_name = "pijp dti"
    step_name = "Mask"
    step_cli = "mask"

    prev_step = [Register]

    def __init__(self, project, code, args):
        super(Mask, self).__init__(project, code, args)
        self.next_step = ApplyMask

    def run(self):
        dat, aff = self._load_nii(self.b0)
        self.logger.info('masking the average b0 volume')
        mask = dtfunc.mask(dat)
        self._save_nii(mask, aff, self.auto_mask)
        mosaic.get_mask_mosaic(self.b0, self.auto_mask, self.mask_mosaic)


class ApplyMask(DTIStep):
    """Apply the auto mask (or the edited one if it exists)
    """

    process_name = "pijp dti"
    step_name = "ApplyMask"
    step_cli = "apply"

    prev_step = [Mask]

    def __init__(self, project, code, args):
        super(ApplyMask, self).__init__(project, code, args)
        self.next_step = TensorFit

    def run(self):
        try:
            reg, reg_aff = self._load_nii(self.reg)


            if os.path.isfile(self.final_mask):
                mask, mask_aff = self._load_nii(self.final_mask)
                self.logger.info('applying the edited mask')
            else:
                mask, mask_aff = self._load_nii(self.auto_mask)
                self.logger.info('applying the auto mask')

            # bin_mask = mask
            # bin_mask[mask > 0] = 1
            # bin_mask[bin_mask < 1] = 0
            masked = dtfunc.apply_mask(reg, mask)
            self._save_nii(masked, mask_aff, self.masked)

        except FileNotFoundError as e:
            self.outcome = 'Error'
            self.comments = str(e)
            self.next_step = None


    @classmethod
    def get_queue(cls, project_name):
        masks = DTIRepository().get_project_masks(project_name)
        todo = [{'ProjectName': project_name, "Code": row['Code']} for row in masks]
        return todo


class TensorFit(DTIStep):
    """Fit the diffusion tensor model
    """
    process_name = "pijp dti"
    step_name = "TensorFit"
    step_cli = "tenfit"
    prev_step = [ApplyMask]

    def __init__(self, project, code, args):
        super(TensorFit, self).__init__(project, code, args)
        self.next_step = Warp

    def run(self):
        dat, aff = self._load_nii(self.masked)
        bval, bvec = self._load_bval_bvec(self.fbval, self.fbvec)
        bvec_reg = np.load(self.fbvec_reg)

        self.logger.info('fitting the tensor')
        evals, evecs, tenfit = dtfunc.fit_dti(dat, bval, bvec_reg)

        self._save_nii(tenfit.fa, aff, self.fa)
        self._save_nii(tenfit.md, aff, self.md)
        self._save_nii(tenfit.ga, aff, self.ga)
        self._save_nii(tenfit.ad, aff, self.ad)
        self._save_nii(tenfit.rd, aff, self.rd)
        self._save_nii(evals, aff, self.evals)
        self._save_nii(evecs, aff, self.evecs)


class Warp(DTIStep):
    """Warp the template FA and labels_lookup to the subject space
    """
    process_name = "pijp dti"
    step_name = "Warp"
    step_cli = "warp"
    prev_step = [TensorFit]

    def __init__(self, project, code, args):
        super(Warp, self).__init__(project, code, args)
        self.next_step = Segment

    def run(self):
        self.logger.info('generating nonlinear registration map for FA')
        fa, fa_aff = self._load_nii(self.fa)
        template, template_aff = self._load_nii(self.template)
        temp_labels, temp_labels_aff = self._load_nii(self.template_labels)

        warped_template, mapping = dtfunc.sym_diff_registration(
            fa, template,
            fa_aff, template_aff)

        warped_labels = mapping.transform(temp_labels, interpolation='nearest')
        warped_fa = mapping.transform_inverse(fa)
        np.save(self.warp_map, mapping.get_forward_field())
        np.save(self.inverse_warp_map, mapping.get_backward_field())
        self._save_nii(warped_fa, template_aff, self.warped_fa)
        self._save_nii(warped_labels, fa_aff, self.warped_labels)
        mosaic.get_warp_mosaic(self.fa, self.warped_labels, self.warp_mosaic)


class Segment(DTIStep):

    process_name = "pijp dti"
    step_name = "Segment"
    step_cli = "seg"
    prev_step = Warp

    def __init__(self, project, code, args):
        super(Segment, self).__init__(project, code, args)
        self.next_step = RoiStats

    def run(self):
        self.logger.info('segmenting tissue for the average b0 of the masked volume')
        if os.path.isfile(self.final_mask):
            mask, maff = self._load_nii(self.final_mask)
        else:
            mask, maff = self._load_nii(self.auto_mask)
        b0, baff = self._load_nii(self.b0)
        masked_b0 = dtfunc.apply_mask(b0, mask)
        segmented = dtfunc.segment_tissue(masked_b0)
        segmented = dtfunc.apply_mask(segmented, mask)  # reapply mask because of noise generated by segmentation
        self._save_nii(segmented, maff, self.segmented)
        mosaic.get_seg_mosaic(self.b0, self.segmented, self.seg_mosaic)


class RoiStats(DTIStep):
    """Generate CSV files for the statistics of various anisotropy measures in certain regions of interest
    """
    process_name = "pijp dti"
    step_name = "RoiStats"
    step_cli = "stats"
    prev_step = [Segment]

    def __init__(self, project, code, args):
        super(RoiStats, self).__init__(project, code, args)

    def run(self):
        self.logger.info('calculating roi statistics')
        fa, aff = self._load_nii(self.fa)
        md, aff = self._load_nii(self.md)
        ga, aff = self._load_nii(self.ga)
        ad, aff = self._load_nii(self.ad)
        rd, aff = self._load_nii(self.rd)
        segmented, aff = self._load_nii(self.segmented)
        warped_labels, aff = self._load_nii(self.warped_labels)
        labels = np.load(self.labels_lookup).item()

        original = nib.load(self.fdwi)
        zooms = original.header.get_zooms()  # Returns the size of the voxels in mm

        measures = {'fa': [fa, self.fa_roi],
                    'md': [md, self.md_roi],
                    'ga': [ga, self.ga_roi],
                    'ad': [ad, self.ad_roi],
                    'rd': [rd, self.rd_roi]}

        for idx in measures.values():
            idx[0][segmented[..., 1] == 0] = 0  # using the second segmented volume TODO better masking? or verify this
            stats = dtfunc.roi_stats(idx[0], warped_labels, labels, zooms)
            self._write_array(stats, idx[1])

    def _write_array(self, array, csv_path):
        with open(csv_path, 'w') as csv_file:
            writer = csv.writer(csv_file)
            for line in array:
                writer.writerow(line)
        self.logger.info("saving {}".format(csv_path))


class MaskQC(DTIStep):
    """Launch a GUI to view a mosaic of all the slices with the skull stripped mask overlaid on the denoised image.
    """
    process_name = "pijp dti"
    step_name = "MaskQC"
    step_cli = "maskqc"
    interactive = True

    def __init__(self, project, code, args):
        super(MaskQC, self).__init__(project, code, args)

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

        if not os.path.isfile(self.final_mask):
                    shutil.copyfile(self.auto_mask, self.final_mask)

        try:
            mask_fig = mosaic.get_mask_mosaic(self.b0, self.auto_mask, self.mask_mosaic)
            (result, comments) = QCinter.run_qc_interface(mask_fig, self.code, edit_cmd=self.open_mask_editor)
            self.outcome = result
            self.comments = comments
            if result == 'pass':
                self.next_step = WarpQC
            elif result == 'fail':
                self.next_step = None
            elif result == 'edit':

                self.outcome = 'edit'
                self.next_step = None
            else:
                self.outcome = 'Error'

        except FileNotFoundError as e:
            self.outcome = 'Error'
            self.comments = str(e)
        finally:
            os.remove(self.review_flag)

    def open_mask_editor(self):
        mask_editor = get_mask_editor()
        cmd = "{mask_editor} -m single {img} {overlay} -t 0.5 -l Red".format(mask_editor=mask_editor, img=self.b0,
                                                                             overlay=self.final_mask)
        self._run_cmd(cmd)

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


class WarpQC(DTIStep):
    """Launch a GUI to view a mosaic of some of the slices with the warped ROI labels_lookup overlaid on the FA image.
    """
    process_name = "pijp dti"
    step_name = "WarpQC"
    step_cli = "warpqc"
    interactive = True
    prev_step = MaskQC

    def __init__(self, project, code, args):
        super(WarpQC, self).__init__(project, code, args)

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
        try:
            mosaic_fig = mosaic.get_warp_mosaic(self.fa, self.warped_labels, self.warp_mosaic)
            (result, comments) = QCinter.run_qc_interface(mosaic_fig, self.code, edit=False)
            self.outcome = result
            self.comments = comments
            if result == 'pass':
                self.next_step = StoreInDatabase
            if result == 'fail':
                self.next_step = None
        finally:
            os.remove(self.review_flag)

    @classmethod
    def get_next(cls, project_name, args):
        cases = DTIRepository().get_warp_qc_list(project_name)
        LOGGER.info("%s cases in queue." % len(cases))

        cases = [x["Code"] for x in cases]
        while len(cases) != 0:
            code = random.choice(cases)
            cases.remove(code)
            next_job = WarpQC(project_name, code, args)
            if not next_job.under_review():
                return next_job


class StoreInDatabase(DTIStep):
    """Store the currently processed information in the database
    """
    process_name = "pijp dti"
    step_name = "StoreInDatabase"
    step_cli = "store"
    interactive = True

    def __init__(self, project, code, args):
        super(StoreInDatabase, self).__init__(project, code, args)

    def run(self):
        self.logger.info("storing in database")
        proj_id = DTIRepository().get_project_id(self.project)  # This returns a dict of {'ProjectID': proj_id}
        proj_id = proj_id['ProjectID']
        DTIRepository().set_roi_stats(proj_id, self.code, self.md_roi, self.fa_roi, self.ga_roi,
                                      self.rd_roi, self.ad_roi)


def run():
    import sys
    current_module = sys.modules[__name__]
    run_module(current_module)


if __name__ == "__main__":
    run_file(os.path.abspath(__file__))
