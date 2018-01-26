import os
import unittest

import numpy as np
import nibabel as nib
from dipy.io import read_bvals_bvecs

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

        dat = np.random.rand(42, 42, 42 ,42)
        aff = np.random.rand(4, 4)
        bval = np.zeros(42)

        avg_b0 = dtfunc.b0_avg(dat, aff, bval)

        self.assertEqual([42, 42, 42], avg_b0.shape)

    def test_register(self):

        dat = np.random.rand(42, 42, 42, 42)
        b0 = np.random.rand(42, 42, 42)
        aff = np.random.rand(4, 4)
        bval = np.zeros(42)
        bvec = np.random.rand(42, 3)

        reg_dat, reg_bvec, reg_map  = dtfunc.register(b0, dat, aff, aff, bval, bvec)
        print(reg_map.shape)

        self.assertEqual(dat.shape, reg_dat.shape)
        self.assertEqual(bvec.shape, reg_bvec.shape)


if __name__ == "__main__":
    unittest.main()
