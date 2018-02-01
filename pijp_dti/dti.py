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
import pymssql
from dipy.io import read_bvals_bvecs
from pijp import util
from pijp.core import Step, get_project_dir
from pijp.repositories import DicomRepository
from pijp.exceptions import ProcessingError, NoLogProcessingError, CancelProcessingError
from pijp.engine import run_module, run_file

import pijp_dti
from pijp_dti import dti_func
from pijp_dti import mosaic, qc_inter
from pijp_dti.repo import DTIRepo

LOGGER = logging.getLogger(__name__)
PROCESS_TITLE = pijp_dti.__process_title__


def get_process_dir(project):
    return os.path.join(get_project_dir(project), PROCESS_TITLE)


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


def get_dcm2nii():
    return '/home/vhasfcellisr/bin/dcm2nii'


class DTIStep(Step):

    def __init__(self, project, code, args):
        super(DTIStep, self).__init__(project, code, args)

        self.working_dir = get_case_dir(project, code)
        self.logdir = os.path.join(get_process_dir(project), 'logs', code)

        # 0Stage
        self.stage_dir = os.path.join(self.working_dir, '0Stage')
        self.fdwi = os.path.join(self.stage_dir, self.code + '.nii.gz')
        self.fbval = os.path.join(self.stage_dir, self.code + '.bval')
        self.fbvec = os.path.join(self.stage_dir, self.code + '.bvec')

        # 1Denoise
        self.den_dir = os.path.join(self.working_dir, '1Denoise')
        self.denoised = os.path.join(self.den_dir, self.code + '_denoised.nii.gz')

        # 2Register
        self.reg_dir = os.path.join(self.working_dir, '2Register')
        self.b0 = os.path.join(self.reg_dir, self.code + '_b0.nii.gz')
        self.reg = os.path.join(self.reg_dir, self.code + '_reg.nii.gz')
        self.fbvec_reg = os.path.join(self.reg_dir, self.code + '_bvec_reg.npy')
        self.reg_map = os.path.join(self.reg_dir, self.code + '_reg_map.npy')

        # 3Mask
        self.mask_dir = os.path.join(self.working_dir, '3Mask')
        self.auto_mask = os.path.join(self.mask_dir, self.code + '_auto_mask.nii.gz')
        self.masked = os.path.join(self.mask_dir, self.code + '_masked.nii.gz')
        self.final_mask = os.path.join(self.mask_dir, self.code + '_final_mask.nii.gz')

        # 4Tenfit
        self.tenfit_dir = os.path.join(self.working_dir, '4Tenfit')
        self.fa = os.path.join(self.tenfit_dir, self.code + '_fa.nii.gz')
        self.md = os.path.join(self.tenfit_dir, self.code + '_md.nii.gz')
        self.ga = os.path.join(self.tenfit_dir, self.code + '_ga.nii.gz')
        self.ad = os.path.join(self.tenfit_dir, self.code + '_ad.nii.gz')
        self.rd = os.path.join(self.tenfit_dir, self.code + '_rd.nii.gz')
        self.evals = os.path.join(self.tenfit_dir, self.code + '_evals.nii.gz')
        self.evecs = os.path.join(self.tenfit_dir, self.code + '_evecs.nii.gz')

        # 5Warp
        self.warp_dir = os.path.join(self.working_dir, '5Warp')
        self.warp_map = os.path.join(self.warp_dir, self.code + '_warp_map.npy')
        self.inverse_warp_map = os.path.join(self.warp_dir, self.code + '_inverse_warp_map.npy')
        self.warped_fa = os.path.join(self.warp_dir, self.code + '_inverse_warped_fa.nii.gz')
        self.warped_labels = os.path.join(self.warp_dir, self.code + '_warped_labels.nii.gz')

        # 6Segment
        self.seg_dir = os.path.join(self.working_dir, '6Segment')
        self.segmented = os.path.join(self.seg_dir, self.code + '_segmented.nii.gz')
        self.segmented_wm = os.path.join(self.seg_dir, self.code + '_segmented_wm.nii.gz')
        self.warped_wm_labels = os.path.join(self.seg_dir, self.code + '_warped_wm_labels.nii.gz')

        # 7Stats
        self.roiavg_dir = os.path.join(self.working_dir, '7Stats')
        self.fa_roi = os.path.join(self.roiavg_dir, self.code + '_fa_roi.csv')
        self.md_roi = os.path.join(self.roiavg_dir, self.code + '_md_roi.csv')
        self.ga_roi = os.path.join(self.roiavg_dir, self.code + '_ga_roi.csv')
        self.ad_roi = os.path.join(self.roiavg_dir, self.code + '_ad_roi.csv')
        self.rd_roi = os.path.join(self.roiavg_dir, self.code + '_rd_roi.csv')

        # 8QC
        self.qc_dir = os.path.join(self.working_dir, '8QC')
        self.mask_mosaic = os.path.join(self.qc_dir, self.code + '_mask_mosaic.png')
        self.warp_mosaic = os.path.join(self.qc_dir, self.code + '_warp.png')
        self.seg_mosaic = os.path.join(self.qc_dir, self.code + '_segment_mosaic.png')

        # 9MNI
        self.mni_dir = os.path.join(self.working_dir, '9MNI')
        self.fa_warp = os.path.join(self.mni_dir, self.code + '_fa_in_mni.nii.gz')
        self.md_warp = os.path.join(self.mni_dir, self.code + '_md_in_mni.nii.gz')
        self.ga_warp = os.path.join(self.mni_dir, self.code + '_ga_in_mni.nii.gz')
        self.ad_warp = os.path.join(self.mni_dir, self.code + '_ad_in_mni.nii.gz')
        self.rd_warp = os.path.join(self.mni_dir, self.code + '_rd_in_mni.nii.gz')

        fpath = os.path.dirname(__file__)
        self.template = os.path.join(fpath, 'templates', 'fa_template.nii')
        self.template_labels = os.path.join(fpath, 'templates', 'fa_labels.nii')
        self.labels_lookup = os.path.join(fpath, 'templates', 'labels.npy')
        self.review_flag = os.path.join(self.working_dir, "qc.inprocess")

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
            self.logger.debug(output.decode('utf-8'))
        if error:
            self.logger.error(error.decode('utf-8'))


class Stage(DTIStep):
    """Convert Dicoms and set up the pipeline."""
    process_name = PROCESS_TITLE
    step_name = "Stage"
    step_cli = "stage"

    def __init__(self, project, code, args):
        super(Stage, self).__init__(project, code, args)
        self.next_step = Denoise

    def run(self):
        self.logger.info("Staging pipeline")
        self.logger.info("Finding DICOM files")
        try:
            source = DicomRepository().get_series_files(self.code)
            if source is None or len(source) == 0:
                raise ProcessingError

            dirs = [self.stage_dir, self.den_dir, self.reg_dir, self.mask_dir, self.tenfit_dir, self.warp_dir,
                    self.seg_dir, self.roiavg_dir, self.qc_dir, self.mni_dir]
            for dr in dirs:
                if not os.path.isdir(dr):
                    os.makedirs(dr)
                    self.logger.info('Building directory {}'.format(dr))

            if len(os.listdir(self.stage_dir)) != 0:
                self.logger.error("{} is not empty!".format(self.stage_dir))
                raise FileExistsError

            else:
                self.convert_with_dcm2niix(source)

            read_bvals_bvecs(self.fbval, self.fbvec)

            if len(nib.load(self.fdwi).get_data().shape) != 4:
                self.outcome = 'Error'
                self.logger.info('DWI must have 4 dimensions')
                self.comments = 'DWI must have 4 dimensions'
                self.next_step = None

        except ProcessingError:
            self.outcome = 'Error'
            self.comments = 'ProcessingError: Could not find staging data.'
            self.logger.error("Could not find the staging data for {}.".format(self.code))
            self.next_step = None

        except FileNotFoundError as e:
            self.outcome = 'Error'
            self.comments = str(e)
            self.logger.error("Can't find files for {}!".format(self.step_name) + '\n' + str(e))
            self.next_step = None

        except FileExistsError as e:
            self.outcome = 'Error'
            self.comments = str(e)
            self.logger.error('Staging directory is not empty. Use --force to reset the case. This will delete '
                              'everything in the case directory!')
            self.next_step = None

    def convert_with_dcm2niix(self, source):
        self.logger.info('Using dcm2niix')
        dcm2niix = get_dcm2niix()
        dcm_dir = self._copy_files(source)
        self.logger.info("Converting DICOM files to NIfTI")
        cmd = '{} -z i -m y -o {} -f {} {}'.format(dcm2niix, self.stage_dir, self.code, dcm_dir)
        self._run_cmd(cmd)

    def convert_with_dcm2nii(self, source):
        self.logger.info('Using dcm2nii')
        dcm2nii = get_dcm2nii()
        dcm_dir = self._copy_files(source)
        self.logger.info("Converting DICOM files to NIfTI")
        cmd = '{} -o {} {}'.format(dcm2nii, self.stage_dir, dcm_dir)
        self._run_cmd(cmd)
        for file in os.listdir(self.stage_dir):  # rename the dcm2nii files
            abs_path = os.path.join(self.stage_dir, file)
            ext = file.split('.')
            ext.pop(0)
            ext = '.' + '.'.join(ext)
            shutil.copyfile(abs_path, os.path.join(self.stage_dir, self.code + ext))
            os.remove(abs_path)

    def reset(self):
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
        staged = DTIRepo().get_staged_cases(project_name)
        dtis = DTIRepo().get_project_dtis(project_name)

        staged_codes = [row['Code'] for row in staged]
        todo = [{'ProjectName': project_name, "Code": row['Code']} for row in dtis if row['Code'] not in
                staged_codes]
        return todo


class Denoise(DTIStep):
    """Denoise the DWI using Local PCA."""
    process_name = PROCESS_TITLE
    step_name = "Denoise"
    step_cli = "denoise"
    prev_step = [Stage]

    def __init__(self, project, code, args):
        super(Denoise, self).__init__(project, code, args)
        self.next_step = Register

    def run(self):
        self.logger.info("Denoising the DWI")
        dat, aff = self._load_nii(self.fdwi)
        bval, bvec = self._load_bval_bvec(self.fbval, self.fbvec)
        denoised = dti_func.denoise_pca(dat, bval, bvec)
        self._save_nii(denoised, aff, self.denoised)


class Register(DTIStep):
    """Rigidly register the DWI to its averaged b0 volume."""
    process_name = PROCESS_TITLE
    step_name = "Register"
    step_cli = "register"
    prev_step = [Denoise]

    def __init__(self, project, code, args):
        super(Register, self).__init__(project, code, args)
        self.next_step = Mask

    def run(self):
        try:
            dat, aff = self._load_nii(self.denoised)
            bval, bvec = self._load_bval_bvec(self.fbval, self.fbvec)
            self.logger.info('Averaging the b0 volume')
            b0 = dti_func.average_b0(dat, aff, bval)
            self.logger.info('Registering the DWI to its averaged b0 volume')
            reg_dat, bvec, reg_map = dti_func.register(b0, dat, aff, aff, bval, bvec)
            self._save_nii(b0, aff, self.b0)
            self._save_nii(reg_dat, aff, self.reg)
            np.save(self.fbvec_reg, bvec)
            np.save(self.reg_map, reg_map)

        except FileNotFoundError as e:
            self.outcome = 'Error'
            self.comments = str(e)
            self.next_step = None
            self.logger.error("Can't find files for {}!".format(self.step_name))


class Mask(DTIStep):
    """Skull strip the average b0 volume."""
    process_name = PROCESS_TITLE
    step_name = "Mask"
    step_cli = "mask"
    prev_step = [Register]

    def __init__(self, project, code, args):
        super(Mask, self).__init__(project, code, args)
        self.next_step = ApplyMask

    def run(self):
        dat, aff = self._load_nii(self.b0)
        self.logger.info('Masking the average b0 volume')
        mask = dti_func.mask(dat)
        self._save_nii(mask, aff, self.auto_mask)
        mosaic.get_mask_mosaic(self.b0, self.auto_mask, self.mask_mosaic)
        shutil.copyfile(self.auto_mask, self.final_mask)


class ApplyMask(DTIStep):
    """Apply the skull stripped mask to the registered image."""
    process_name = PROCESS_TITLE
    step_name = "ApplyMask"
    step_cli = "apply"

    prev_step = [Mask]

    def __init__(self, project, code, args):
        super(ApplyMask, self).__init__(project, code, args)
        self.next_step = TensorFit

    def run(self):
        try:
            self.logger.info('Applying the mask')
            reg, reg_aff = self._load_nii(self.reg)
            mask, mask_aff = self._load_nii(self.final_mask)
            masked = dti_func.apply_mask(reg, mask)
            self._save_nii(masked, mask_aff, self.masked)
            if DTIRepo().is_edited(self.project, self.code):
                self.outcome = 'Redone'

        except FileNotFoundError as e:
            self.outcome = 'Error'
            self.comments = str(e)
            self.next_step = None
            self.logger.error("Can't find files for {}!".format(self.step_name))

    @classmethod
    def get_queue(cls, project_name):
        masks = DTIRepo().get_edited_masks(project_name)
        todo = [{'ProjectName': project_name, "Code": row['Code']} for row in masks]
        return todo


class TensorFit(DTIStep):
    """Fit the diffusion tensor model."""
    process_name = PROCESS_TITLE
    step_name = "TensorFit"
    step_cli = "tenfit"
    prev_step = [ApplyMask]

    def __init__(self, project, code, args):
        super(TensorFit, self).__init__(project, code, args)
        self.next_step = Warp

    def run(self):
        self.logger.info('Fitting the tensor')
        dat, aff = self._load_nii(self.masked)
        bval, bvec = self._load_bval_bvec(self.fbval, self.fbvec)
        bvec_reg = np.load(self.fbvec_reg)
        evals, evecs, tenfit = dti_func.fit_dti(dat, bval, bvec_reg)
        self._save_nii(tenfit.fa, aff, self.fa)
        self._save_nii(tenfit.md, aff, self.md)
        self._save_nii(tenfit.ga, aff, self.ga)
        self._save_nii(tenfit.ad, aff, self.ad)
        self._save_nii(tenfit.rd, aff, self.rd)
        self._save_nii(evals, aff, self.evals)
        self._save_nii(evecs, aff, self.evecs)

        if DTIRepo().is_edited(self.project, self.code):
                self.outcome = 'Redone'


class Warp(DTIStep):
    """Warp the template FA and template Labels to the subject space."""
    process_name = PROCESS_TITLE
    step_name = "Warp"
    step_cli = "warp"
    prev_step = [TensorFit]

    def __init__(self, project, code, args):
        super(Warp, self).__init__(project, code, args)
        self.next_step = Segment

    def run(self):
        self.logger.info('Generating nonlinear registration map for FA')
        fa, fa_aff = self._load_nii(self.fa)
        template, template_aff = self._load_nii(self.template)
        temp_labels, temp_labels_aff = self._load_nii(self.template_labels)

        warped_template, mapping = dti_func.sym_diff_registration(
            fa, template,
            fa_aff, template_aff)

        warped_labels = mapping.transform(temp_labels, interpolation='nearest')
        warped_fa = mapping.transform_inverse(fa)
        np.save(self.warp_map, mapping.get_forward_field())
        np.save(self.inverse_warp_map, mapping.get_backward_field())
        self._save_nii(warped_fa, template_aff, self.warped_fa)
        self._save_nii(warped_labels, fa_aff, self.warped_labels)

        if DTIRepo().is_edited(self.project, self.code):
                self.outcome = 'Redone'


class Segment(DTIStep):
    """Segment the tissue for the average b0 volume."""
    process_name = PROCESS_TITLE
    step_name = "Segment"
    step_cli = "seg"
    prev_step = Warp

    def __init__(self, project, code, args):
        super(Segment, self).__init__(project, code, args)
        self.next_step = RoiStats

    def run(self):
        self.logger.info('Segmenting tissue for the average b0 of the masked volume')
        mask, maff = self._load_nii(self.final_mask)
        b0, baff = self._load_nii(self.b0)
        warped, waff = self._load_nii(self.warped_labels)
        masked_b0 = dti_func.apply_mask(b0, mask)
        segmented = dti_func.segment_tissue(masked_b0)
        segmented_wm = dti_func.apply_tissue_mask(masked_b0, segmented, prob=1)
        warped_wm_labels = dti_func.apply_tissue_mask(warped, segmented, prob=1)
        self._save_nii(segmented, baff, self.segmented)
        self._save_nii(segmented_wm, baff, self.segmented_wm)
        self._save_nii(warped_wm_labels, waff, self.warped_wm_labels)
        mosaic.get_seg_mosaic(self.b0, self.segmented_wm, self.seg_mosaic)
        mosaic.get_warp_mosaic(self.fa, self.warped_wm_labels, self.warp_mosaic)
        if DTIRepo().is_edited(self.project, self.code):
                self.outcome = 'Redone'


class RoiStats(DTIStep):
    """Generate CSV files for DTI statistics."""
    process_name = PROCESS_TITLE
    step_name = "RoiStats"
    step_cli = "stats"
    prev_step = [Segment]

    def __init__(self, project, code, args):
        super(RoiStats, self).__init__(project, code, args)

    def run(self):
        self.logger.info('Calculating roi statistics')
        fa, aff = self._load_nii(self.fa)
        md, aff = self._load_nii(self.md)
        ga, aff = self._load_nii(self.ga)
        ad, aff = self._load_nii(self.ad)
        rd, aff = self._load_nii(self.rd)
        warped_wm_labels, aff = self._load_nii(self.warped_wm_labels)
        roi_labels = np.load(self.labels_lookup).item()  # dict of int values and ROI names
        original = nib.load(self.fdwi)
        zooms = original.header.get_zooms()  # Returns the size of the voxels in mm

        measures = {'fa': [fa, self.fa_roi],
                    'md': [md, self.md_roi],
                    'ga': [ga, self.ga_roi],
                    'ad': [ad, self.ad_roi],
                    'rd': [rd, self.rd_roi]}

        for idx in measures.values():
            stats = dti_func.roi_stats(idx[0], warped_wm_labels, roi_labels, zooms)
            self._write_array(stats, idx[1])

        if DTIRepo().is_edited(self.project, self.code):
                self.outcome = 'Redone'

    def _write_array(self, array, csv_path):
        with open(csv_path, 'w') as csv_file:
            writer = csv.writer(csv_file)
            for line in array:
                writer.writerow(line)
        self.logger.info("saving {}".format(csv_path))


class MaskQC(DTIStep):
    """Launch a GUI to QC the skull stripping."""
    process_name = PROCESS_TITLE
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
        try:
            if not os.path.isfile(self.b0) or not os.path.isfile(self.auto_mask) or not os.path.isfile(self.final_mask):
                raise FileNotFoundError

            result, comments = qc_inter.run(self.code, self.b0, self.auto_mask, self.final_mask,
                                            self.step_name)
            self.outcome = result
            self.comments = comments
            if result == 'pass':
                self.next_step = SegQC

            if result == 'cancelled':
                self.outcome = 'Cancelled'
                self.logger.info("Cancelled")
                raise CancelProcessingError

            if result == 'skipped':
                self.outcome = 'Cancelled'
                self.comments = 'Skipped'
                self.logger.info("Skipped {}".format(self.code))

        except FileNotFoundError as e:
            self.outcome = 'Error'
            self.comments = str(e)
            self.logger.error("Can't find files for {}!".format(self.step_name))
            raise CancelProcessingError

        finally:
            os.remove(self.review_flag)

    @classmethod
    def get_next(cls, project_name, args):
        cases = DTIRepo().get_masks_to_qc(project_name)
        LOGGER.info("%s cases in queue." % len(cases))

        cases = [x["Code"] for x in cases]
        last_job = DTIRepo().find_where_left_off(project_name, 'MaskQC')

        while len(cases) != 0:
            if (last_job
                    and last_job['Outcome'] == 'Cancelled'
                    and last_job['Comments'] != 'Skipped'):
                code = last_job["Code"]
                cases.remove(code)
                next_job = MaskQC(project_name, code, args)
            else:
                code = random.choice(cases)
                cases.remove(code)
                next_job = MaskQC(project_name, code, args)
            if not next_job.under_review():
                return next_job


class SegQC(DTIStep):
    """Launch a GUI to QC the segmentation."""
    process_name = PROCESS_TITLE
    step_name = "SegQC"
    step_cli = 'segqc'
    interactive = True
    prev_step = 'MaskQC'

    def __init__(self, project, code, args):
        super(SegQC, self).__init__(project, code, args)

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
            if not os.path.isfile(self.b0) or not os.path.isfile(self.segmented_wm):
                raise FileNotFoundError

            (result, comments) = qc_inter.run(self.code, self.b0, self.segmented_wm, self.segmented_wm,
                                              self.step_name)
            self.outcome = result
            self.comments = comments
            if result == 'pass':
                self.next_step = WarpQC
            if result == 'fail':
                self.next_step = None
            if result == 'cancelled':
                self.outcome = 'Cancelled'
                self.logger.info("Cancelled")
                raise CancelProcessingError
            if result == 'skipped':
                self.outcome = 'Skipped'
                self.logger.info("Skipped {}".format(self.code))

        except FileNotFoundError as e:
            self.outcome = 'Error'
            self.comments = str(e)
            self.logger.error("Can't find files for {}!".format(self.step_name))
            raise CancelProcessingError

        finally:
            os.remove(self.review_flag)

    @classmethod
    def get_next(cls, project_name, args):
        cases = DTIRepo().get_segs_to_qc(project_name)
        LOGGER.info("%s cases in queue." % len(cases))

        cases = [x["Code"] for x in cases]
        while len(cases) != 0:
            code = random.choice(cases)
            cases.remove(code)
            next_job = SegQC(project_name, code, args)
            if not next_job.under_review():
                return next_job


class WarpQC(DTIStep):
    """Launch a GUI to QC the non-linear registration."""
    process_name = PROCESS_TITLE
    step_name = "WarpQC"
    step_cli = "warpqc"
    interactive = True

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
            if not os.path.isfile(self.fa) or not os.path.isfile(self.warped_wm_labels):
                raise FileNotFoundError

            (result, comments) = qc_inter.run(self.code, self.fa, self.warped_wm_labels,
                                              self.warped_wm_labels, self.step_name)
            self.outcome = result
            self.comments = comments
            if result == 'pass':
                self.next_step = StoreInDatabase
            if result == 'fail':
                self.next_step = None
            if result == 'cancelled':
                self.outcome = 'Cancelled'
                self.logger.info("Cancelled")
                raise CancelProcessingError
            if result == 'skipped':
                self.outcome = 'Skipped'
                self.logger.info("Skipped {}".format(self.code))

        except FileNotFoundError as e:
            self.outcome = 'Error'
            self.comments = str(e)
            self.logger.error("Can't find files for {}!".format(self.step_name))
            raise CancelProcessingError

        finally:
            os.remove(self.review_flag)

    @classmethod
    def get_next(cls, project_name, args):
        cases = DTIRepo().get_warps_to_qc(project_name)
        LOGGER.info("%s cases in queue." % len(cases))

        cases = [x["Code"] for x in cases]
        while len(cases) != 0:
            code = random.choice(cases)
            cases.remove(code)
            next_job = WarpQC(project_name, code, args)
            if not next_job.under_review():
                return next_job


class StoreInDatabase(DTIStep):
    """Store the ROI statistics in the database."""
    process_name = PROCESS_TITLE
    step_name = "StoreInDatabase"
    step_cli = "store"
    interactive = True

    def __init__(self, project, code, args):
        super(StoreInDatabase, self).__init__(project, code, args)

    def run(self):
        self.logger.info("Storing in database")
        proj_id = DTIRepo().get_project_id(self.project)  # This returns a dict of {'ProjectID': proj_id}
        proj_id = proj_id['ProjectID']

        try:
            DTIRepo().set_roi_stats(proj_id, self.code, self.md_roi, self.fa_roi, self.ga_roi,
                                    self.rd_roi, self.ad_roi)

        except pymssql.IntegrityError as e:
            self.outcome = 'Error'
            self.comments = str(e)
            self.logger.error("Code {} is already in the database! Use --force to reset.".format(self.code))

    def reset(self):
        self.logger.info("Removing {} from database".format(self.code))
        DTIRepo().remove_roi_stats(self.project, self.code)


class SaveInMNI(DTIStep):
    """Warp the subject's anisotropy measures to MNI space."""
    process_name = PROCESS_TITLE
    step_name = "SaveInMNI"
    step_cli = "mni"

    def __init__(self, project, code, args):
        super(SaveInMNI, self).__init__(project, code, args)

    def run(self):
        self.logger.info("Saving in MNI space")

        # inverse_warp_map = np.load(self.inverse_warp_map)
        template, template_aff = self._load_nii(self.template)
        fa, aff = self._load_nii(self.fa)
        md, aff = self._load_nii(self.md)
        ga, aff = self._load_nii(self.ga)
        rd, aff = self._load_nii(self.rd)
        ad, aff = self._load_nii(self.ad)
        # Have to redo warping... want to eventually do the transform just with the inverse_warp_map
        warped_template, mapping = dti_func.sym_diff_registration(fa, template, aff, template_aff)
        fa_warp = mapping.transform_inverse(fa)
        md_warp = mapping.transform_inverse(md)
        ga_warp = mapping.transform_inverse(ga)
        rd_warp = mapping.transform_inverse(rd)
        ad_warp = mapping.transform_inverse(ad)
        self._save_nii(fa_warp, aff, self.fa_warp)
        self._save_nii(md_warp, aff, self.md_warp)
        self._save_nii(ga_warp, aff, self.ga_warp)
        self._save_nii(rd_warp, aff, self.rd_warp)
        self._save_nii(ad_warp, aff, self.ad_warp)


def run():
    import sys
    current_module = sys.modules[__name__]
    run_module(current_module)


if __name__ == "__main__":
    run_file(os.path.abspath(__file__))
