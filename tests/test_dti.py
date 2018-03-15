import unittest
import os

from pijp_dti import dti


class Test(unittest.TestCase):

    project = 'NRC'
    code = 'NRC-FRA018-0003-V0-a1001'
    args = None

    def test_stage(self):

        stage = dti.Stage(self.project, self.code, self.args)
        stage.run()

        self.assertTrue(os.path.isdir(stage.stage_dir))
        self.assertTrue(os.path.isdir(stage.reg_dir))
        self.assertTrue(os.path.isdir(stage.den_dir))
        self.assertTrue(os.path.isdir(stage.mask_dir))
        self.assertTrue(os.path.isdir(stage.tenfit_dir))
        self.assertTrue(os.path.isdir(stage.warp_dir))
        self.assertTrue(os.path.isdir(stage.roiavg_dir))
        self.assertTrue(os.path.isfile(stage.fdwi))
        self.assertTrue(os.path.isfile(stage.fbval))
        self.assertTrue(os.path.isfile(stage.fbvec))

    def test_denoise(self):

        denoise = dti.Denoise(self.project, self.code, self.args)
        denoise.run()

        self.assertTrue(os.path.isfile(denoise.denoised))

    def test_register(self):

        register = dti.Register(self.project, self.code, self.args)
        register.run()

        self.assertTrue(os.path.isfile(register.b0))
        self.assertTrue(os.path.isfile(register.reg))
        self.assertTrue(os.path.isfile(register.fbvec_reg))

    def test_mask(self):

        mask = dti.Mask(self.project, self.code, self.args)
        mask.run()

        self.assertTrue(os.path.isfile(mask.auto_mask))

    def test_apply_mask(self):

        apply_mask = dti.ApplyMask(self.project, self.code, self.args)
        apply_mask.run()

        self.assertTrue(os.path.isfile(apply_mask.masked))

    def test_tenfit(self):

        tenfit = dti.TensorFit(self.project, self.code, self.args)
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
        warp.run()

        self.assertTrue(os.path.isfile(warp.warped_fa))
        self.assertTrue(os.path.isfile(warp.warped_labels))
        self.assertTrue(os.path.isfile(warp.warp_map))

    def test_segment(self):

        seg = dti.Segment(self.project, self.code, self.args)
        seg.run()

        self.assertTrue(os.path.isfile(seg.segmented))

    def test_roi_stats(self):

        stats = dti.RoiStats(self.project, self.code, self.args)
        stats.run()

        self.assertTrue(os.path.isfile(stats.fa_roi))
        self.assertTrue(os.path.isfile(stats.md_roi))
        self.assertTrue(os.path.isfile(stats.ga_roi))
        self.assertTrue(os.path.isfile(stats.rd_roi))
        self.assertTrue(os.path.isfile(stats.ad_roi))

    def test_mask_qc(self):

        mask_qc = dti.MaskQC(self.project, self.code, self.args)
        mask_qc.run()

        self.assertIsNotNone(mask_qc.outcome)

    def test_seg_qc(self):

        seg_qc = dti.SegQC(self.project, self.code, self.args)
        seg_qc.run()

        self.assertIsNotNone(seg_qc.outcome)

    def test_warp_qc(self):

        warp_qc = dti.WarpQC(self.project, self.code, self.args)
        warp_qc.run()

        self.assertIsNotNone(warp_qc.outcome)

    def test_save_in_mni(self):

        save_in_mni = dti.SaveInMNI(self.project, self.code, self.args)
        save_in_mni.run()

        self.assertTrue(os.path.isfile(save_in_mni.fa_warp))
        self.assertTrue(os.path.isfile(save_in_mni.md_warp))
        self.assertTrue(os.path.isfile(save_in_mni.ga_warp))
        self.assertTrue(os.path.isfile(save_in_mni.ad_warp))
        self.assertTrue(os.path.isfile(save_in_mni.rd_warp))
