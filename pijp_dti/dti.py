import csv
import os
import tempfile
import shutil
import pickle
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
from pijp.engine import run_module, run_file
from pijp.exceptions import (ProcessingError, NoLogProcessingError,
                             CancelProcessingError)
from pijp_nnicv.nnicv import SkullStripStep

import pijp_dti
from pijp_dti import dti_func, qc_main, qc_func
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
    dcm2niix = util.configuration['dcm2niix']['path']
    if not os.path.isfile(dcm2niix):
        raise FileNotFoundError
    return dcm2niix


def get_dcm2nii():
    dcm2nii = util.configuration['dcm2nii']['path']
    if not os.path.isfile(dcm2nii):
        raise FileNotFoundError
    return dcm2nii


class DTIStep(Step):

    def __init__(self, project, code, args):
        """Base Step __init__ method.

        This method initializes all the file path strings used by the
        different steps. The various paths are sorted by they directory name
        where they will be stored.

        Args:
            project (str): The name of the project.
            code (str): The code for the image.
            args (str): Optional arguments.

        """
        super(DTIStep, self).__init__(project, code, args)
        self.cpu = 2
        self.mem = 2048
        self.working_dir = get_case_dir(project, code)
        self.logdir = os.path.join(get_process_dir(project), 'logs', code)

        # 0Stage
        self.stage_dir = os.path.join(self.working_dir, '0Stage')
        self.fdwi = os.path.join(self.stage_dir, self.code + '.nii.gz')
        self.fbval = os.path.join(self.stage_dir, self.code + '.bval')
        self.fbvec = os.path.join(self.stage_dir, self.code + '.bvec')

        # 1Denoise
        self.den_dir = os.path.join(self.working_dir, '1Denoise')
        self.denoised = os.path.join(
            self.den_dir, self.code + '_denoised.nii.gz')

        # 2Register
        self.reg_dir = os.path.join(self.working_dir, '2Register')
        self.b0 = os.path.join(self.reg_dir, self.code + '_b0.nii.gz')
        self.reg = os.path.join(self.reg_dir, self.code + '_reg.nii.gz')
        self.fbvec_orig = os.path.join(self.reg_dir, self.code +
                                       '_bvec_orig.csv')
        self.fbvec_reg = os.path.join(self.reg_dir, self.code +
                                      '_bvec_reg.csv')
        self.fbval_csv = os.path.join(self.reg_dir, self.code +
                                      '_bval.csv')
        self.reg_map = os.path.join(self.reg_dir, self.code + '_reg_map.p')

        # 3Mask
        self.mask_dir = os.path.join(self.working_dir, '3Mask')
        self.nnicv = os.path.join(self.mask_dir, self.code + '_nnicv.nii.gz')
        self.nnicv_reg = os.path.join(self.mask_dir, self.code +
                                      '_nnicv_reg.nii.gz')
        self.t2 = os.path.join(self.mask_dir, self.code + '_t2.nii.gz')
        self.t2_reg = os.path.join(self.mask_dir, self.code + '_t2_reg.nii.gz')

        self.auto_mask = os.path.join(
            self.mask_dir, self.code + '_auto_mask.nii.gz')
        self.final_mask = os.path.join(
            self.mask_dir, self.code + '_final_mask.nii.gz')

        self.masked = os.path.join(self.mask_dir, self.code + '_masked.nii.gz')

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
        self.warp_map = os.path.join(
            self.warp_dir, self.code + '_warp_map.p')
        self.warped_fa = os.path.join(
            self.warp_dir, self.code + '_inverse_warped_fa.nii.gz')
        self.warped_labels = os.path.join(
            self.warp_dir, self.code + '_warped_labels.nii.gz')

        # 6Segment
        self.seg_dir = os.path.join(self.working_dir, '6Segment')
        self.segmented = os.path.join(
            self.seg_dir, self.code + '_segmented.nii.gz')
        self.segmented_wm = os.path.join(
            self.seg_dir, self.code + '_segmented_wm.nii.gz')
        self.warped_wm_labels = os.path.join(
            self.seg_dir, self.code + '_warped_wm_labels.nii.gz')

        # 7Stats
        self.roiavg_dir = os.path.join(self.working_dir, '7Stats')
        self.fa_roi = os.path.join(self.roiavg_dir, self.code + '_fa_roi.csv')
        self.md_roi = os.path.join(self.roiavg_dir, self.code + '_md_roi.csv')
        self.ga_roi = os.path.join(self.roiavg_dir, self.code + '_ga_roi.csv')
        self.ad_roi = os.path.join(self.roiavg_dir, self.code + '_ad_roi.csv')
        self.rd_roi = os.path.join(self.roiavg_dir, self.code + '_rd_roi.csv')

        # 8MNI
        self.mni_dir = os.path.join(self.working_dir, '8MNI')
        self.fa_warp = os.path.join(
            self.mni_dir, self.code + '_fa_in_mni.nii.gz')
        self.md_warp = os.path.join(
            self.mni_dir, self.code + '_md_in_mni.nii.gz')
        self.ga_warp = os.path.join(
            self.mni_dir, self.code + '_ga_in_mni.nii.gz')
        self.ad_warp = os.path.join(
            self.mni_dir, self.code + '_ad_in_mni.nii.gz')
        self.rd_warp = os.path.join(
            self.mni_dir, self.code + '_rd_in_mni.nii.gz')

        # templates
        fpath = os.path.dirname(__file__)
        self.template = os.path.join(fpath, 'templates', 'fa_template.nii')
        self.template_labels = os.path.join(
            fpath, 'templates', 'fa_labels.nii')
        self.labels_lookup = os.path.join(fpath, 'templates', 'labels.npy')
        self.review_flag = os.path.join(self.working_dir, "qc.inprocess")

    def _load_nii(self, fname):
        try:
            self.logger.info('loading {}'.format(fname.split('/')[-1]))
            img = nib.load(fname)
            img = nib.as_closest_canonical(img)
            dat = img.get_data()
            aff = img.affine
            return dat, aff

        except FileNotFoundError as e:
            self.logger.info(str(e))
            self.outcome = 'Error'
            self.comments = str(e)
            raise e

    def _load_bval_bvec(self, fbval, fbvec):
        try:
            self.logger.info(f"loading {fbval.split('/')[-1]} "
                             f"{fbvec.split('/')[-1]}")

            bval, bvec = read_bvals_bvecs(fbval, fbvec)
            return bval, bvec

        except IOError as e:
            self.logger.info(str(e))
            self.outcome = 'Error'
            self.comments = str(e)
            raise e

    def _save_nii(self, dat, aff, fname):
        self.logger.info(f"saving {fname.split('/')[-1]}")
        img = nib.Nifti1Image(dat, aff)
        img.to_filename(fname)

    def _run_cmd(self, cmd):
        self.logger.debug(cmd)
        args = cmd.split()
        p = subprocess.Popen(
            args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        (output, error) = p.communicate()
        if output:
            self.logger.debug(output.decode('utf-8'))
        if error:
            self.logger.error(error.decode('utf-8'))


class BaseQCStep(DTIStep):
    """The base step for QC steps.

    The BaseQCStep contains the basic attributes and functions used by all
    qc steps. Attributes are set using `set_qc_params` instead of `__init__` as
    not interfere with the `pijp` engine.

    Attributes:
        image (str): Path to the base image.
        mode (str): The type of QC for the step.
        overlay (str): Path to the final image overlay (to be edited)
        overlay_original (str): Path to the original copy of the overlay.

    """

    def __init__(self, project, code, args):
        super(BaseQCStep, self).__init__(project, code, args)
        self.image = None
        self.mode = None
        self.overlay = None
        self.overlay_original = None
        self.disable_edit = None
        self.pass_step = None
        self.edit_step = None

    def set_qc_params(self):
        """Need to set these parameters for QC Main to work

            self.image
            self.mode
            self.overlay
            self.overlay_original
            self.disable_edit
            self.pass_step
            self.edit_step

        """
        self.logger.warning('This set_qc_params(), it does nothing!')

    def under_review(self):
        if os.path.exists(self.review_flag):
            self._print_review_info()
            return True
        return False

    def _print_review_info(self):
        flag = open(self.review_flag, 'r')
        lines = flag.readlines()
        flag.close()
        self.logger.info('{} is under review by {} starting {}'.format(
            self.code, lines[0].rstrip('\n'), lines[1]))

    def initiate(self):
        if self.under_review():
            raise NoLogProcessingError(
                "This case is currently being reviewed.")
        flag = open(self.review_flag, 'w')
        flag.write(
            getpass.getuser() + '\n' + datetime.datetime.now().strftime('%c'))
        flag.close()

    def run(self):
        """Runs the step `MaskQC`.

        Opens a GUI for quality control. The qc_main.main method should
        return a tuple (result, comments). `result` should be a string of
        'pass', 'fail', 'edit', or 'cancelled'. `comments` should be a string.

        """
        try:
            self.set_qc_params()

            result, comments = qc_main.main(
                self.project, self.code, self.mode,
                self.image, self.overlay, self.overlay_original,
                disable_edit=self.disable_edit)
            self.outcome = result
            self.comments = comments

            if result == 'Pass':
                self.next_step = self.pass_step
            if result == 'Edit':
                self.next_step = self.edit_step
            if result == 'Cancelled':
                self.outcome = 'Cancelled'
                self.logger.info("Cancelled")
                if comments != 'skipped':
                    raise CancelProcessingError

        except FileNotFoundError as e:
            self.outcome = 'fail'
            self.comments = str(e)
            self.logger.info('Failed! ' + str(e))

        finally:
            os.remove(self.review_flag)

    def reset(self):
        os.remove(self.review_flag)


class Stage(DTIStep):
    """Convert Dicoms and set up the pipeline."""
    process_name = PROCESS_TITLE
    step_name = "Stage"
    step_cli = "stage"

    def __init__(self, project, code, args):
        super(Stage, self).__init__(project, code, args)
        self.next_step = Denoise

    def run(self):
        """Runs the step `Stage`.

        Creates the directories for all the steps. Finds the DICOMs for the
        code in the database, copies them  to a temporary directory,
        then finally converts them to the Nifti format using dcm2nii/dcm2niix.
        The staged files are stored in the `0Stage` directory and are
        verified as an Diffusion Weighted Image (DWI).

        """
        self.logger.info("Staging pipeline")
        self.logger.info("Finding DICOM files")
        try:
            source = DicomRepository().get_series_files(self.code)
            if source is None or len(source) == 0:
                raise ProcessingError

            dirs = [self.stage_dir, self.den_dir, self.reg_dir,
                    self.mask_dir, self.tenfit_dir, self.warp_dir,
                    self.seg_dir, self.roiavg_dir, self.mni_dir]

            self.logger.info('Building directories')
            [os.makedirs(dr) for dr in dirs if not os.path.isdir(dr)]

            if len(os.listdir(self.stage_dir)) != 0:
                self.logger.error("Staging directory is not empty!")
                raise FileExistsError

            else:
                self._convert_with_dcm2niix(source)

            dat, aff = self._load_nii(self.fdwi)
            self._save_nii(dat, aff, self.fdwi)
            read_bvals_bvecs(self.fbval, self.fbvec)  # Raises IOError if not

            if len(dat.shape) != 4:
                self.outcome = 'Error'
                self.comments = (f"{self.fdwi} has {dat.shape} dimension(s). "
                                 f"DWI must have 4 dimensions.")
                self.logger.info(self.comments)
                self.next_step = None

        except FileNotFoundError:
            self.next_step = None

        except IOError:
            self.next_step = None

        except ProcessingError:
            self.outcome = 'Error'
            self.comments = f"Could not find the staging data for {self.code}."
            self.logger.error(self.comments)
            self.next_step = None

        except FileExistsError as e:
            self.outcome = 'Error'
            self.comments = str(e)
            self.logger.error(
                'Staging directory is not empty. '
                'Use --force to reset the case. '
                'This will delete everything in the case directory!')
            self.next_step = None

    def _convert_with_dcm2niix(self, source):
        self.logger.info('Using dcm2niix')
        dcm2niix = get_dcm2niix()
        dcm_dir = self._copy_files(source)
        self.logger.info("Converting DICOM files to NIfTI")
        cmd = f"{dcm2niix} -z i -m y -o {self.stage_dir} " \
              f"-f {self.code} {dcm_dir}"

        self._run_cmd(cmd)

    def _convert_with_dcm2nii(self, source):
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
            shutil.copyfile(
                abs_path, os.path.join(self.stage_dir, self.code + ext))
            os.remove(abs_path)

    def reset(self):
        shutil.rmtree(
            get_case_dir(self.project, self.code), ignore_errors=True)

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
        todo = [{'ProjectName': project_name, "Code": row['Code']}
                for row in dtis if row['Code'] not in staged_codes]

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
        """Runs the step `Denoise`.

        Loads all the staged data. Denoises the staged DWI by calling
        a denoising function.

        """
        try:
            # Loading
            dat, aff = self._load_nii(self.fdwi)
            bval, bvec = self._load_bval_bvec(self.fbval, self.fbvec)

            # Running
            self.logger.info("Denoising the DWI")
            denoised = dti_func.denoise_pca(dat, bval, bvec)

            # Saving
            self._save_nii(denoised, aff, self.denoised)

        except FileNotFoundError:
            self.next_step = None
        except IOError:
            self.next_step = None


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
        """Runs the step `Register`

        The b0 is generated by finding all the b0's in the DWI and rigidly
        registers them to the first found b0 volume. The rest of the diffusion
        weighted volumes are then registered to the averaged b0 volume.

        """
        try:
            # Loading
            dat, aff = self._load_nii(self.denoised)
            bval, bvec = self._load_bval_bvec(self.fbval, self.fbvec)

            # Running
            self.logger.info('Averaging the b0 volume')
            b0 = dti_func.average_b0(dat, aff, bval)
            self.logger.info('Registering the DWI to its averaged b0 volume')
            reg_dat, bvec_reg, reg_map = dti_func.register(
                b0, dat, aff, aff, bval, bvec)

            # Saving
            self._save_nii(b0, aff, self.b0)
            self._save_nii(reg_dat, aff, self.reg)
            np.savetxt(self.fbvec_reg, bvec_reg, delimiter=",")
            np.savetxt(self.fbval_csv, bval, delimiter=",")
            np.savetxt(self.fbvec_orig, bvec, delimiter=".")
            with open(self.reg_map, "wb") as f:
                pickle.dump(reg_map, f)

        except FileNotFoundError:
            self.next_step = None
        except IOError:
            self.next_step = None


class Mask(DTIStep):
    """Skull strip the average b0 volume."""
    process_name = PROCESS_TITLE
    step_name = "Mask"
    step_cli = "mask"
    prev_step = [Register]

    def __init__(self, project, code, args):
        super(Mask, self).__init__(project, code, args)

    def run(self):
        """Runs the step `Mask`.
_
        Loads the average b0 and generates a binary mask of the brain using
        a median Otsu method. The generated mask is copied as a `final_mask`
        for QC editing.

        """
        try:
            # Loading
            dat, aff = self._load_nii(self.b0)

            use_nnicv = DTIRepo().get_project_settings(self.project)[
                'UseNNICV']

            scancode = DTIRepo().get_scancode(self.code)
            t1_code = DTIRepo().get_t1(self.project, scancode)

            if t1_code and use_nnicv:
                # Instantiate NNICV base step, get paths from there
                ss_step = SkullStripStep(self.project, t1_code, self.args)
                nnicv_path = ss_step.final_icv_mask
                t2_path = ss_step.t2_path
                status = DTIRepo().get_nnicv_status(self.project, t1_code)
                # Running
                if os.path.isfile(nnicv_path) and status != 'Fail':

                    self.logger.info('Found NNICV mask!')
                    shutil.copyfile(nnicv_path, self.nnicv)
                    shutil.copyfile(t2_path, self.t2)

                    nnicv, naff = self._load_nii(self.nnicv)
                    t2, taff = self._load_nii(self.t2)

                    self.logger.info('Warping T2 to average b0')
                    t2_reg, tmap = dti_func.sym_diff_registration(
                        dat, t2, aff, taff)
                    self.logger.info('Applying transform to NNICV mask')
                    mask = tmap.transform(nnicv, interpolation='nearest')
                    self._save_nii(t2_reg, aff, self.t2_reg)

                    if status == 'Pass' or status == 'Edit':
                        self.comments = "Used NNICV final mask."
                    else:
                        self.comments = "Used NNICV auto mask."

                else:
                    self.logger.info('Masking the average b0 volume')
                    mask = dti_func.mask(dat)
                    if status == "Fail":
                        self.comments = "Found failed NNICV mask. Used Otsu mask."
                    elif not t1_code:
                        self.comments = "Couldn't Find T1! Used Otsu mask."
                    else:
                        self.comments = "Couldn't find NNICV mask! Used Otsu mask."

            else:
                self.logger.info('Masking the average b0 volume')
                mask = dti_func.mask(dat)
                self.comments = "Used Otsu mask."

            # Saving
            if os.path.isfile(self.auto_mask) and os.path.isfile(
                    self.final_mask):
                if qc_func.masks_are_same(self.auto_mask, self.final_mask):
                    self._save_nii(mask, aff, self.auto_mask)
                    shutil.copyfile(self.auto_mask, self.final_mask)
                else:
                    self.outcome = 'Error'
                    self.logger.error("Mask has already been edited! "
                                      "Use --force to reset.")
                    self.comments = "Mask has already been edited!"

            elif not os.path.isfile(self.auto_mask):
                self._save_nii(mask, aff, self.auto_mask)
                shutil.copyfile(self.auto_mask, self.final_mask)

        except FileNotFoundError:
            self.next_step = None

    def reset(self):
        os.remove(self.final_mask)

    @classmethod
    def get_queue(cls, project_name):

        if DTIRepo().get_project_settings(project_name)['UseNNICV']:
            staged = DTIRepo().get_staged_cases(project_name)
            nnicv = DTIRepo().get_finished_nnicv(project_name)
            staged_nnicv = DTIRepo().get_staged_nnicv(project_name)
            finished_mask_qc = DTIRepo().get_finished_mask_qc(project_name)
            failed_masks = DTIRepo().get_failed_mask(project_name)

            todo = [
                {'ProjectName': project_name, "Code": row["Code"]}
                for row in staged
                if {'Code': str(
                    DTIRepo().get_t1(project_name, row["Code"]))} in nnicv
                and row not in staged_nnicv
                and row not in finished_mask_qc
                and row not in failed_masks
            ]

            return todo


class MaskQC(BaseQCStep):
    """Launch a GUI to QC the skull stripping."""
    process_name = PROCESS_TITLE
    step_name = "MaskQC"
    step_cli = "maskqc"
    interactive = True

    def __init__(self, project, code, args):
        super(MaskQC, self).__init__(project, code, args)

    def set_qc_params(self):
        self.image = self.b0
        self.mode = self.step_name
        self.overlay = self.final_mask
        self.overlay_original = self.auto_mask
        self.disable_edit = False
        self.pass_step = ApplyMask
        self.edit_step = ApplyMask

    @classmethod
    def get_next(cls, project_name, args):
        cases = DTIRepo().get_masks_to_qc(project_name)
        unfinished_nnicv = DTIRepo().get_unfinished_nnicv(project_name)
        finished_mask_qc = DTIRepo().get_finished_mask_qc(project_name)

        if DTIRepo().get_project_settings(project_name)['UseNNICV']:
            cases = [
                x["Code"] for x in cases
                if DTIRepo().get_t1(project_name, x["Code"])
                not in unfinished_nnicv
                and x["Code"] not in finished_mask_qc
            ]
        else:
            cases = [
                x["Code"] for x in cases if x["Code"] not in finished_mask_qc
            ]

        LOGGER.info("%s cases in queue." % len(cases))

        last_job = DTIRepo().find_where_left_off(project_name, 'MaskQC')

        while len(cases) != 0:
            if (last_job
                    and last_job['Outcome'] == 'Cancelled'
                    and last_job['Comments'] != 'skipped'):
                code = last_job["Code"]
                if code in cases:
                    cases.remove(code)
                next_job = MaskQC(project_name, code, args)
            else:
                code = random.choice(cases)
                if code in cases:
                    cases.remove(code)
                next_job = MaskQC(project_name, code, args)

            if not next_job.under_review():
                return next_job


class ApplyMask(DTIStep):
    """Apply the skull stripped mask to the registered image."""
    process_name = PROCESS_TITLE
    step_name = "ApplyMask"
    step_cli = "apply"

    prev_step = [MaskQC]

    def __init__(self, project, code, args):
        super(ApplyMask, self).__init__(project, code, args)
        self.next_step = TensorFit

    def run(self):
        """Runs the step `ApplyMask`

        Masks the registered DWI using the final mask,  whether or not it
        was edited.

        """
        try:
            # Loading
            reg, reg_aff = self._load_nii(self.reg)
            mask, mask_aff = self._load_nii(self.final_mask)

            # Running
            self.logger.info('Applying the mask')
            masked = dti_func.apply_mask(reg, mask)

            # Saving
            self._save_nii(masked, mask_aff, self.masked)

        except FileNotFoundError:
            self.next_step = None


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
        """Runs the step `TensorFit`

        Fits the Diffusion Tensor model using the denoised, registered,
        and  masked DWI. The dti_func.fit_dti method returns `evals`,
        `evecs`, and a `tenfit` object. `evals` and `evecs` are numpy
        ndarrays that can be saved as Nifti images. They are used to
        calculate the various measures of anisotropy. The `tenfit` object
        already generates these measures (as ndarrays), and they are also
        saved as Nifti images.

        """
        try:
            # Loading
            dat, aff = self._load_nii(self.masked)
            bval, bvec = self._load_bval_bvec(self.fbval, self.fbvec)
            bvec_reg = np.loadtxt(self.fbvec_reg, delimiter=",")

            # Running
            self.logger.info('Fitting the tensor')
            evals, evecs, tenfit = dti_func.fit_dti(dat, bval, bvec_reg)

            # Saving
            self._save_nii(tenfit.fa, aff, self.fa)
            self._save_nii(tenfit.md, aff, self.md)
            self._save_nii(tenfit.ga, aff, self.ga)
            self._save_nii(tenfit.ad, aff, self.ad)
            self._save_nii(tenfit.rd, aff, self.rd)
            self._save_nii(evals, aff, self.evals)
            self._save_nii(evecs, aff, self.evecs)

        except FileNotFoundError:
            self.next_step = None
        except IOError:
            self.next_step = None


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
        """Runs the step `Warp`

        Loads a template FA in MNI space and its associated label overlay.
        The values of the label overlay are integers that are mapped to
        regions of interest (ROI) names in a lookup table. The template FA
        is warped to the subject FA space using nonlinear registration (
        symmetric diffeomorphic registration). The same warp mapping is
        used to transform the templates' overlay labels to the subject space.

        """
        try:
            # Loading
            fa, fa_aff = self._load_nii(self.fa)
            template, template_aff = self._load_nii(self.template)
            temp_labels, temp_labels_aff = self._load_nii(self.template_labels)

            # Runnning
            self.logger.info('Warping template to FA')
            warped_template, mapping = dti_func.sym_diff_registration(
                fa, template,
                fa_aff, template_aff)
            warped_labels = mapping.transform(
                temp_labels, interpolation='nearest')
            warped_fa = mapping.transform_inverse(fa)

            # Saving
            with open(self.warp_map, "wb") as f:
                pickle.dump(mapping, f)
            self._save_nii(warped_fa, template_aff, self.warped_fa)
            self._save_nii(warped_labels, fa_aff, self.warped_labels)

        except FileNotFoundError:
            self.next_step = None


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
        """Runs the step `Segment`

        Creates a white matter segmentation mask based on the masked average
        b0. The white matter segmentation is applied to the warped labels.

        """
        try:
            # Loading
            b0, baff = self._load_nii(self.b0)
            mask, faff = self._load_nii(self.final_mask)
            warped, waff = self._load_nii(self.warped_labels)

            # Running
            self.logger.info(
                'Segmenting tissue for the masked volume')
            masked_b0 = dti_func.apply_mask(b0, mask)

            if os.path.isfile(self.t2_reg):
                t2_reg, taff = self._load_nii(self.t2_reg)
                masked_t2 = dti_func.apply_mask(t2_reg, mask)
                segmented = dti_func.segment_tissue(masked_t2)
            else:
                segmented = dti_func.segment_tissue(masked_b0)

            segmented_wm = dti_func.apply_tissue_mask(
                masked_b0, segmented, prob=1)
            warped_wm_labels = dti_func.apply_tissue_mask(
                warped, segmented, prob=1)

            # Saving
            self._save_nii(segmented, baff, self.segmented)
            self._save_nii(segmented_wm, baff, self.segmented_wm)
            self._save_nii(warped_wm_labels, waff, self.warped_wm_labels)

        except FileNotFoundError:
            self.next_step = None


class RoiStats(DTIStep):
    """Generate CSV files for DTI statistics."""
    process_name = PROCESS_TITLE
    step_name = "RoiStats"
    step_cli = "stats"
    prev_step = [Segment]

    def __init__(self, project, code, args):
        super(RoiStats, self).__init__(project, code, args)

    def run(self):
        """Runs the step `RoiStats`

        Loads the various measures of anisotropy, the white matter segmented
        labels, and the lookup table for the labels. The  ROI statistics
        are only calculated inside the label mask and where value of measure
        is not zero. The statistics are saved as separate CSVs for each
        measure.

        """
        try:
            # Loading
            fa, aff = self._load_nii(self.fa)
            md, aff = self._load_nii(self.md)
            ga, aff = self._load_nii(self.ga)
            ad, aff = self._load_nii(self.ad)
            rd, aff = self._load_nii(self.rd)
            warped_wm_labels, aff = self._load_nii(self.warped_wm_labels)
            # dict of int values and ROI names
            roi_labels = np.load(self.labels_lookup).item()
            original = nib.load(self.fdwi)
            zooms = original.header.get_zooms()  # Returns voxel size

            # Running and Saving
            measures = {'fa': [fa, self.fa_roi],
                        'md': [md, self.md_roi],
                        'ga': [ga, self.ga_roi],
                        'ad': [ad, self.ad_roi],
                        'rd': [rd, self.rd_roi]}

            self.logger.info('Calculating roi statistics')
            for idx in measures.values():
                stats = dti_func.roi_stats(
                    idx[0], warped_wm_labels, roi_labels, zooms)
                self._write_array(stats, idx[1])

        except FileNotFoundError:
            self.next_step = None

    def _write_array(self, array, csv_path):
        with open(csv_path, 'w') as csv_file:
            writer = csv.writer(csv_file)
            for line in array:
                writer.writerow(line)
        self.logger.info("saving {}".format(csv_path))


class SegQC(BaseQCStep):
    """Launch a GUI to QC the segmentation."""
    process_name = PROCESS_TITLE
    step_name = "SegQC"
    step_cli = 'segqc'
    interactive = True

    def __init__(self, project, code, args):
        super(SegQC, self).__init__(project, code, args)

    def set_qc_params(self):
        self.image = self.b0
        self.mode = self.step_name
        self.overlay = self.segmented_wm
        self.overlay_original = self.segmented_wm
        self.disable_edit = True
        self.pass_step = WarpQC

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


class WarpQC(BaseQCStep):
    """Launch a GUI to QC the non-linear registration."""
    process_name = PROCESS_TITLE
    step_name = "WarpQC"
    step_cli = "warpqc"
    interactive = True

    def __init__(self, project, code, args):
        super(WarpQC, self).__init__(project, code, args)

    def set_qc_params(self):
        self.image = self.fa
        self.mode = self.step_name
        self.overlay = self.warped_wm_labels
        self.overlay_original = self.warped_wm_labels
        self.disable_edit = True
        self.pass_step = StoreInDatabase


class StoreInDatabase(DTIStep):
    """Store the ROI statistics in the database."""
    process_name = PROCESS_TITLE
    step_name = "StoreInDatabase"
    step_cli = "store"
    interactive = True

    def __init__(self, project, code, args):
        super(StoreInDatabase, self).__init__(project, code, args)

        if DTIRepo().get_project_settings(self.project)['SaveMNI']:
            self.next_step = SaveInMNI
        else:
            self.next_step = None

    def run(self):
        """Runs `StoreInDatabase`

        Loads the CSVs and stores them in a single database table.

        """

        self.logger.info("Storing in database")
        proj_id = DTIRepo().get_project_id(self.project)

        try:
            if DTIRepo().check_seg_qc_pass(
                    self.project, self.code) == 'Pass':
                if DTIRepo().check_warp_qc_pass(
                        self.project, self.code) == 'Pass':

                    DTIRepo().set_roi_stats(proj_id, self.code, self.md_roi,
                                            self.fa_roi, self.ga_roi,
                                            self.rd_roi, self.ad_roi)

                else:
                    self.outcome = 'Error'
                    self.logger.error(f"{self.code} did not pass WarpQC!")
            else:
                self.outcome = 'Error'
                self.logger.error(f"{self.code} did not pass SegQC!")

        except pymssql.IntegrityError as e:
            self.outcome = 'Error'
            self.comments = str(e)
            self.logger.error(f"Code {self.code} is already in the database! "
                              f"Use --force to reset.")
            self.next_step = None

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
        try:
            # Loading
            fa, aff = self._load_nii(self.fa)
            md, aff = self._load_nii(self.md)
            ga, aff = self._load_nii(self.ga)
            rd, aff = self._load_nii(self.rd)
            ad, aff = self._load_nii(self.ad)
            with open(self.warp_map, "rb") as f:
                mapping = pickle.load(f)

            # Running
            self.logger.info("Warping to MNI space")
            fa_warp = mapping.transform_inverse(fa)
            md_warp = mapping.transform_inverse(md)
            ga_warp = mapping.transform_inverse(ga)
            rd_warp = mapping.transform_inverse(rd)
            ad_warp = mapping.transform_inverse(ad)

            # Saving
            self._save_nii(fa_warp, aff, self.fa_warp)
            self._save_nii(md_warp, aff, self.md_warp)
            self._save_nii(ga_warp, aff, self.ga_warp)
            self._save_nii(rd_warp, aff, self.rd_warp)
            self._save_nii(ad_warp, aff, self.ad_warp)

        except FileNotFoundError as e:
            self.outcome = 'Fail'
            self.comments = str(e)
            self.next_step = None


def run():
    import sys
    current_module = sys.modules[__name__]
    run_module(current_module)


if __name__ == "__main__":
    run_file(os.path.abspath(__file__))
