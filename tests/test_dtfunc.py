import unittest

import numpy as np
import nibabel as nib
from dipy.io import read_bvals_bvecs

from pijp_dti import dtfunc


class Test(unittest.TestCase):

    def test_denoise(self):

        img = nib.load('/home/vhasfcellisr/Ryan/test/t2/test2.nii.gz')

        dat = img.get_data()

        den = dtfunc.denoise(dat)

        self.assertEqual(den.shape, dat.shape)
        self.assertLess(den.sum(), dat.sum())

    def test_b0_avg(self):
        img = nib.load('/home/vhasfcellisr/Ryan/test/t4/test4.nii.gz')
        bval, bvec = read_bvals_bvecs('/home/vhasfcellisr/Ryan/test/t1/test1.bval', None)
        dat = img.get_data()
        aff = img.affine
        b0 = dtfunc.b0_avg(dat, aff, bval)
        self.assertEqual(b0.shape, dat[..., 0].shape)

    def test_register(self):

        img = nib.load('/home/vhasfcellisr/Ryan/test/t1/test1.nii.gz')
        bval, bvec = read_bvals_bvecs('/home/vhasfcellisr/Ryan/test/t1/test1.bval',
                                      '/home/vhasfcellisr/Ryan/test/t1/test1.bvec')
        dat = img.get_data()
        aff = img.affine

        b0 = dtfunc.b0_avg(dat, aff, bval)

        reg_dat, reg_bvecs = dtfunc.register(b0, dat, aff, aff, bval, bvec)

        self.assertEqual(dat.shape, reg_dat.shape)

    def test_fit_dti(self):

        img = nib.load('/home/vhasfcellisr/Ryan/test/t1/test1.nii.gz')
        bval, bvec = read_bvals_bvecs('/home/vhasfcellisr/Ryan/test/t1/test1.bval',
                                      '/home/vhasfcellisr/Ryan/test/t1/test1.bvec')
        dat = img.get_data()

        evals, evecs, tenfit = dtfunc.fit_dti(dat, bval, bvec)

        self.assertEqual(dat[...,0].shape, tenfit.fa.shape)

        pass

if __name__ == "__main__":
    unittest.main()
