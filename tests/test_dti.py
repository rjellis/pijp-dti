import unittest
import os

from pijp_dti import dti


class Test(unittest.TestCase):

    project = 'PPMI'
    code = 'PPMI_007_S_3107m12_i296434'
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
        self.assertTrue(os.path.isdir(stage.qc_dir))
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
        self.assertTrue(os.path.isfile(mask.mask_mosaic))

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
        self.assertTrue(os.path.isfile(warp.inverse_warp_map))

    def test_segment(self):

        seg = dti.Segment(self.project, self.code, self.args)
        seg.run()

        self.assertTrue(os.path.isfile(seg.segmented))

    def test_roistats(self):

        stats = dti.RoiStats(self.project, self.code, self.args)
        stats.run()

        self.assertTrue(os.path.isfile(stats.fa_roi))
        self.assertTrue(os.path.isfile(stats.md_roi))
        self.assertTrue(os.path.isfile(stats.ga_roi))
        self.assertTrue(os.path.isfile(stats.rd_roi))
        self.assertTrue(os.path.isfile(stats.ad_roi))

    def test_maskqc(self):

        maskqc = dti.MaskQC(self.project, self.code, self.args)
        maskqc.run()

        self.assertIsNotNone(maskqc.outcome)

    def test_segqc(self):

        segqc = dti.SegQC(self.project, self.code, self.args)
        segqc.run()

        self.assertIsNotNone(segqc.outcome)

    def test_warpqc(self):

        warpqc = dti.WarpQC(self.project, self.code, self.args)
        warpqc.run()

        self.assertIsNotNone(warpqc.outcome)

    def test_saveinmni(self):

        saveinmni = dti.SaveInMNI(self.project, self.code, self.args)
        saveinmni.run()

        self.assertTrue(os.path.isfile(saveinmni.fa_warp))
        self.assertTrue(os.path.isfile(saveinmni.md_warp))
        self.assertTrue(os.path.isfile(saveinmni.ga_warp))
        self.assertTrue(os.path.isfile(saveinmni.ad_warp))
        self.assertTrue(os.path.isfile(saveinmni.rd_warp))
