import unittest
import os
import shutil

from pijp_dti import dti

class Test(unittest.TestCase):

    project = 'NRC'
    code = 'NRC-FRA018-0003-V0-a1001'
    args = None
    working_dir = '/home/vhasfcellisr/tests/'
    logdir = '/home/vhasfcellisr/tests'
    comments = 'testing'

    def test_stage(self):

        stage = dti.Stage(self.project, self.code, self.args)
        stage.working_dir = self.working_dir
        stage.logdir = self.logdir
        stage.run()

        self.assertTrue(os.path.isdir(os.path.join(stage.working_dir, 'stage')))
        self.assertTrue(os.path.isdir(os.path.join(stage.working_dir, 'register')))
        self.assertTrue(os.path.isdir(os.path.join(stage.working_dir, 'denoise')))
        self.assertTrue(os.path.isdir(os.path.join(stage.working_dir, 'mask')))
        self.assertTrue(os.path.isdir(os.path.join(stage.working_dir, 'tenfit')))
        self.assertTrue(os.path.isdir(os.path.join(stage.working_dir, 'warp')))
        self.assertTrue(os.path.isdir(os.path.join(stage.working_dir, 'stats')))
        self.assertTrue(os.path.isdir(os.path.join(stage.working_dir, 'qc')))
        self.assertTrue(os.path.isfile(stage.fdwi))
        self.assertTrue(os.path.isfile(stage.fbval))
        self.assertTrue(os.path.isfile(stage.fbvec))

    def test_denoise(self):

        denoise = dti.Denoise(self.project, self.code, self.args)
        denoise.working_dir = self.working_dir
        denoise.logdir = self.logdir
        denoise.run()

        self.assertTrue(os.path.isfile(denoise.denoised))

    def test_register(self):

        register = dti.Register(self.project, self.code, self.args)
        register.working_dir = self.working_dir
        register.logdir = self.logdir
        register.run()

        self.assertTrue(os.path.isfile(register.b0))
        self.assertTrue(os.path.isfile(register.reg))
        self.assertTrue(os.path.isfile(register.fbvec_reg))

    def test_mask(self):

        mask = dti.Mask(self.project, self.code, self.args)
        mask.working_dir = self.working_dir
        mask.logdir = self.logdir
        mask.run()

        self.assertTrue(os.path.isfile(mask.auto_mask))
        self.assertTrue(os.path.isfile(mask.mask_mosaic))

    def test_apply_mask(self):

        apply_mask = dti.ApplyMask(self.project, self.code, self.args)
        apply_mask.working_dir = self.working_dir
        apply_mask.logdir = self.logdir
        apply_mask.run()

        self.assertTrue(os.path.isfile(apply_mask.masked))

    def test_tenfit(self):

        tenfit = dti.TensorFit(self.project, self.code, self.args)
        tenfit.working_dir = self.working_dir
        tenfit.logdir = self.logdir
        tenfit.run()

        self.assertTrue(os.path.isfile(tenfit.fa))
        self.assertTrue(os.path.isfile(tenfit.md))
        self.assertTrue(os.path.isfile(tenfit.ga))
        self.assertTrue(os.path.isfile(tenfit.rd))
        self.assertTrue(os.path.isfile(tenfit.ad))
        self.assertTrue(os.path.isfile(tenfit.evecs))
        self.assertTrue(os.path.isfile(tenfit.evals))

    def test_warp(self):

        warp = dti.Warp(self.project, self.code, self.args)
        warp.working_dir = self.working_dir
        warp.logdir = self.logdir
        warp.run()

        self.assertTrue(os.path.isfile(warp.warped_fa))
        self.assertTrue(os.path.isfile(warp.warped_labels))
        self.assertTrue(os.path.isfile(warp.warp_map))
        self.assertTrue(os.path.isfile(warp.inverse_warp_map))

    def test_segment(self):

        seg = dti.Segment(self.project, self.code, self.args)
        seg.working_dir = self.working_dir
        seg.logdir = self.logdir
        seg.run()

        self.assertTrue(os.path.isfile(seg.segmented))

    def test_roistats(self):

        stats = dti.RoiStats(self.project, self.code, self.args)
        stats.working_dir = self.working_dir
        stats.logdir = self.logdir
        stats.run()

        self.assertTrue(os.path.isfile(stats.fa_roi))
        self.assertTrue(os.path.isfile(stats.md_roi))
        self.assertTrue(os.path.isfile(stats.ga_roi))
        self.assertTrue(os.path.isfile(stats.rd_roi))
        self.assertTrue(os.path.isfile(stats.ad_roi))
