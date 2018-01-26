import unittest

import numpy as np

from pijp_dti import dtfunc


class Test(unittest.TestCase):

    def test_mask(self):

        dat = np.random.rand(42, 42, 42)
        masked = dtfunc.mask(dat)

        self.assertEqual(masked.shape, dat.shape)

    def test_apply_mask(self):

        dat = np.random.rand(42, 42, 42)
        bin_mask = np.random.randint(0, 1, size=(42, 42, 42), dtype='bool')
        masked = dtfunc.apply_mask(dat, bin_mask)

        self.assertEqual(dat.shape, masked.shape)

    def test_denoise(self):

        dat = np.random.rand(42, 42, 42, 42)
        denoised = dtfunc.denoise(dat)

        self.assertEqual(dat.shape, denoised.shape)

    def test_denoise_pca(self):

        dat = np.random.rand(42, 42, 42, 42)
        bval = np.zeros(42)
        bvec = np.random.rand(42, 3)
        denoised = dtfunc.denoise_pca(dat, bval, bvec)

        self.assertEqual(dat.shape, denoised.shape)

    def test_b0_avg(self):

        dat = np.random.rand(42, 42, 42, 42)
        aff = np.random.rand(4, 4)
        bval = np.zeros(42)

        avg_b0 = dtfunc.b0_avg(dat, aff, bval)

        self.assertEqual((42, 42, 42), avg_b0.shape)

    def test_register(self):

        dat = np.random.rand(42, 42, 42, 42)
        b0 = np.random.rand(42, 42, 42)
        aff = np.random.rand(4, 4)
        bval = np.zeros(42)
        bvec = np.random.rand(42, 3)

        reg_dat, reg_bvec, reg_map = dtfunc.register(b0, dat, aff, aff, bval, bvec)

        self.assertEqual(dat.shape, reg_dat.shape)
        self.assertEqual(bvec.shape, reg_bvec.shape)

    def test_fit_dti(self):
        dat = np.random.rand(42, 42, 42, 42)
        bval = np.zeros(42)
        bvec = np.random.rand(42, 3)

        evals, evecs, tenfit = dtfunc.fit_dti(dat, bval, bvec)

        self.assertEqual(dat[..., 0].shape, tenfit.fa.shape)  # fa should be 3D
        self.assertEqual(dat[..., 0].shape + (3,), evals.shape)  # should have 3 eigenvalues per voxel for 3D image
        self.assertEqual(dat[..., 0].shape + (3, 3), evecs.shape)  # should have 3 eigenvectors per voxel for 3D image

    def test_segment_tissue(self):

        dat = np.random.rand(42, 42, 42)

        segmented = dtfunc.segment_tissue(dat)

        self.assertEqual(dat.shape + (4,), segmented.shape)

    def test_apply_tissue_mask(self):

        dat = np.random.rand(42, 42, 42)
        segmented = np.random.rand(42, 42, 42, 4)

        segmented_dat = dtfunc.apply_tissue_mask(dat, segmented)

        self.assertEqual(dat.shape, segmented_dat.shape)

    def test_affine_registration(self):

        static = np.random.rand(42, 42, 42)
        moving = np.random.rand(42, 42, 42)
        static_affine = np.random.rand(4, 4)
        moving_affine = np.random.rand(4, 4)

        reg, reg_aff, aff_map = dtfunc.affine_registration(static, moving, static_affine, moving_affine)

        self.assertEqual(static.shape, reg.shape)

    def test_sym_diff_registration(self):

        static = np.random.rand(42, 42, 42)
        moving = np.random.rand(42, 42, 42)
        static_affine = np.random.rand(4, 4)
        moving_affine = np.random.rand(4, 4)

        # DIV BY 0 Error somewhere in dipy.align.imwarp
        # TODO: fix random data
        warped, warped_mapping = dtfunc.sym_diff_registration(static, moving, static_affine, moving_affine)

        self.assertEqual(static.shape, warped.shape)


if __name__ == "__main__":
    unittest.main()
