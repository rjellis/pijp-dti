import unittest

import numpy as np
import nibabel as nib
from dipy.io import read_bvals_bvecs

from pijp_dti import dtfunc
from pijp_dti import dtiQC


class Test(unittest.TestCase):

    def test_mask(self):
        img = nib.load('/home/vhasfcellisr/Ryan/test/t2/test2.nii.gz')
        dat = img.get_data()
        # dat = dtfunc.denoise(dat)
        b0 = dat[..., 0]
        b0 = dtiQC.rescale(b0)
        b0 = np.stack((b0, b0, b0), axis=-1)

        mask = dtfunc.mask(dat)
        mask = mask[..., 0]

        masked = dtiQC.mask_image(b0.astype(float), mask, hue=[0, 1, 0], alpha=0.7)

        fig = dtiQC.Nifti_Animator(masked)
        fig.plot()


    def test_denoise(self):

        img = nib.load('/home/vhasfcellisr/Ryan/test/t1/test1.nii.gz')

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

        self.assertEqual(dat[..., 0].shape, tenfit.fa.shape)

        pass


if __name__ == "__main__":
    unittest.main()
