import unittest

import numpy as np
import nibabel as nib
from dipy.io import read_bvals_bvecs

from pijp_dti import dtfunc


class Test(unittest.TestCase):

    def test_mask(self):
        dat_2d_square = np.random.rand(10, 10)
        dat_2d_not_square = np.random.rand(10, 30)
        dat_3d_square = np.random.rand(30, 30, 30)
        dat_3d_not_square = np.random.rand(30, 60, 20)

        self.assertEqual(dtfunc.mask(dat_2d_square).shape, dat_2d_square.shape)
        self.assertEqual(dtfunc.mask(dat_2d_not_square).shape, dat_2d_not_square.shape)
        self.assertEqual(dtfunc.mask(dat_3d_square).shape, dat_3d_square.shape)
        self.assertEqual(dtfunc.mask(dat_3d_not_square).shape, dat_3d_not_square.shape)

    def test_denoise(self):

        dat_3d_square = np.random.rand(30, 30, 30)
        dat_3d_not_square = np.random.rand(30, 30, 31)

        self.assertEqual(dtfunc.denoise(dat_3d_square).shape, dat_3d_square.shape)
        self.assertEqual(dtfunc.denoise(dat_3d_not_square).shape, dat_3d_not_square.shape)

    def test_b0_avg(self):
        img = nib.load('/home/vhasfcellisr/Ryan/test/t4/test4.nii.gz')
        bval, bvec = read_bvals_bvecs('/home/vhasfcellisr/Ryan/test/t4/test4.bval', None)
        dat = img.get_data()
        aff = img.affine
        b0 = dtfunc.b0_avg(dat, aff, bval)
        self.assertEqual(b0.shape, dat[..., 0].shape)

    def test_register(self):

        img = nib.load('/home/vhasfcellisr/Ryan/test/t4/test4.nii.gz')
        bval, bvec = read_bvals_bvecs('/home/vhasfcellisr/Ryan/test/t4/test4.bval',
                                      '/home/vhasfcellisr/Ryan/test/t4/test4.bvec')
        dat = img.get_data()
        aff = img.affine

        b0 = dtfunc.b0_avg(dat, aff, bval)

        reg_dat, reg_bvecs = dtfunc.register(b0, dat, aff, aff, bval, bvec)

        self.assertEqual(dat.shape, reg_dat.shape)

    def test_fit_dti(self):
        pass

    def test_roi_stats(self):
        pass

    def test_affine_registration(self):
        pass

    def test_sym_diff_registration(self):
        pass


if __name__ == "__main__":
    unittest.main()
