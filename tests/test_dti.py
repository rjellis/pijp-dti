import unittest
import os

from pijp_dti import dti


class Test(unittest.TestCase):

    # A working Project/Code
    project = 'sample_project'
    code = 'sample_code'
    args = None

    # A nonexistent Project/Code
    bad_proj = 'not_a_project'
    bad_code = 'not_a_code'

    def test_stage(self):

        stage = dti.Stage(self.project, self.code, self.args)
        stage.run()
        bad_stage = dti.Stage(self.bad_proj, self.bad_code, self.args)
        bad_stage.run()

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
        self.assertEqual(bad_stage.outcome, 'Error')

    def test_denoise(self):

        denoise = dti.Denoise(self.project, self.code, self.args)
        denoise.run()
        bad_denoise = dti.Denoise(self.bad_proj, self.bad_code, self.args)
        bad_denoise.run()

        self.assertTrue(os.path.isfile(denoise.denoised))
        self.assertEqual(bad_denoise.outcome, 'Error')

    def test_register(self):

        register = dti.Register(self.project, self.code, self.args)
        register.run()
        bad_register = dti.Register(self.bad_proj, self.bad_code, self.args)
        bad_register.run()

        self.assertTrue(os.path.isfile(register.b0))
        self.assertTrue(os.path.isfile(register.reg))
        self.assertTrue(os.path.isfile(register.fbvec_reg))
        self.assertEqual(bad_register.outcome, 'Error')

    def test_mask(self):

        mask = dti.Mask(self.project, self.code, self.args)
        mask.run()
        bad_mask = dti.Mask(self.bad_proj, self.bad_code, self.args)
        bad_mask.run()

        self.assertTrue(os.path.isfile(mask.auto_mask))
        self.assertTrue(os.path.isfile(mask.mask_mosaic))
        self.assertEqual(bad_mask.outcome, 'Error')

    def test_apply_mask(self):

        apply_mask = dti.ApplyMask(self.project, self.code, self.args)
        apply_mask.run()
        bad_apply_mask = dti.ApplyMask(self.bad_proj, self.bad_code, self.args)
        bad_apply_mask.run()

        self.assertTrue(os.path.isfile(apply_mask.masked))
        self.assertEqual(bad_apply_mask.outcome, 'Error')

    def test_tenfit(self):

        tenfit = dti.TensorFit(self.project, self.code, self.args)
        tenfit.run()
        bad_tenfit = dti.TensorFit(self.bad_proj, self.bad_code, self.args)
        bad_tenfit.run()

        self.assertTrue(os.path.isfile(tenfit.fa))
        self.assertTrue(os.path.isfile(tenfit.md))
        self.assertTrue(os.path.isfile(tenfit.ga))
        self.assertTrue(os.path.isfile(tenfit.rd))
        self.assertTrue(os.path.isfile(tenfit.ad))
        self.assertTrue(os.path.isfile(tenfit.evecs))
        self.assertTrue(os.path.isfile(tenfit.evals))
        self.assertEqual(bad_tenfit.outcome, 'Error')

    def test_warp(self):

        warp = dti.Warp(self.project, self.code, self.args)
        warp.run()
        bad_warp = dti.Warp(self.bad_proj, self.bad_code, self.args)
        bad_warp.run()

        self.assertTrue(os.path.isfile(warp.warped_fa))
        self.assertTrue(os.path.isfile(warp.warped_labels))
        self.assertTrue(os.path.isfile(warp.warp_map))
        self.assertTrue(os.path.isfile(warp.inverse_warp_map))
        self.assertEqual(bad_warp.outcome, 'Error')

    def test_segment(self):

        seg = dti.Segment(self.project, self.code, self.args)
        seg.run()
        bad_seg = dti.Segment(self.bad_proj, self.bad_code, self.args)
        bad_seg.run()

        self.assertTrue(os.path.isfile(seg.segmented))
        self.assertEqual(bad_seg.outcome, 'Error')

    def test_roistats(self):

        stats = dti.RoiStats(self.project, self.code, self.args)
        stats.run()
        bad_stats = dti.RoiStats(self.bad_proj, self.bad_code, self.args)
        bad_stats.run()

        self.assertTrue(os.path.isfile(stats.fa_roi))
        self.assertTrue(os.path.isfile(stats.md_roi))
        self.assertTrue(os.path.isfile(stats.ga_roi))
        self.assertTrue(os.path.isfile(stats.rd_roi))
        self.assertTrue(os.path.isfile(stats.ad_roi))
        self.assertEqual(bad_stats.outcome, 'Error')

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
        bad_saveinmni = dti.SaveInMNI(self.bad_proj, self.bad_code, self.args)
        bad_saveinmni.run()

        self.assertTrue(os.path.isfile(saveinmni.fa_warp))
        self.assertTrue(os.path.isfile(saveinmni.md_warp))
        self.assertTrue(os.path.isfile(saveinmni.ga_warp))
        self.assertTrue(os.path.isfile(saveinmni.ad_warp))
        self.assertTrue(os.path.isfile(saveinmni.rd_warp))
        self.assertEqual(bad_saveinmni.outcome, 'Error')
