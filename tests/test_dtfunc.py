import os
import unittest

import numpy as np
import nibabel as nib
from dipy.io import read_bvals_bvecs

from pijp_dti import dtfunc


class Test(unittest.TestCase):
    code = 'NRC-FRA018-0003-V0-a1001'
    img1 = '/m/InProcess/External/NRC/pijp_dti/{code}/0Stage/{code}.nii.gz'.format(code=code)
    fbval = '/m/InProcess/External/NRC/pijp_dti/{code}/0Stage/{code}.bval'.format(code=code)
    fbvec = '/m/InProcess/External/NRC/pijp_dti/{code}/0Stage/{code}.bvec'.format(code=code)

    fpath = os.path.dirname(__file__).rstrip('/tests') + '/pijp_dti'
    template = os.path.join(fpath, 'templates', 'fa_template.nii')
    template_labels = os.path.join(fpath, 'templates', 'fa_labels.nii')
    labels_lookup = os.path.join(fpath, 'templates', 'labels.npy')

    def test_mask(self):
        dat = nib.load(self.img1).get_data()
        masked = dtfunc.mask(dat)

        self.assertEqual(masked.shape, dat.shape)

    def test_denoise(self):
        dat = nib.load(self.img1).get_data()
        bval, bvec = read_bvals_bvecs(self.fbval, self.fbvec)
        denoised = dtfunc.denoise_pca(dat, bval, bvec)

        self.assertEqual(denoised.shape, dat.shape)

    def test_b0_avg(self):

        dat = nib.load(self.img1).get_data()
        aff = nib.load(self.img1).affine
        bval, bvec = read_bvals_bvecs(self.fbval, self.fbvec)
        b0 = dtfunc.b0_avg(dat, aff, bval)

        img = nib.Nifti1Image(b0, aff)
        nib.save(img, '/home/vhasfcellisr/b0_avg.nii')

        self.assertEqual(b0.shape, dat[..., 0].shape)

    def test_affine_registration(self):

        dat = nib.load(self.img1).get_data()
        aff = nib.load(self.img1).affine
        a = dat[:, :, :, 0]
        b = dat[:, :, :, 1]

        reg, aff_reg, aff_map = dtfunc.affine_registration(a, b, aff, aff)

        c = nib.Nifti1Image(reg, aff_reg)
        nib.save(c, '/home/vhasfcellisr/reg_1.nii')

    def test_register(self):

        dat = nib.load(self.img1).get_data()
        aff = nib.load(self.img1).affine
        bval, bvec = read_bvals_bvecs(self.fbval, self.fbvec)
        dat_b0 = dtfunc.b0_avg(dat, aff, bval)
        reg, bvecs = dtfunc.register(dat_b0, dat, aff, aff, bval, bvec)

        self.assertEqual(reg.shape, dat.shape)

    def test_fit_dti(self):

        dat = nib.load(self.img1).get_data()
        bval, bvec = read_bvals_bvecs(self.fbval, self.fbvec)
        evals, evecs, tenfit = dtfunc.fit_dti(dat, bval, bvec)

        self.assertEqual(len(tenfit.fa), len(dat[..., 0]))
        print(len(tenfit.fa), len(dat[..., 0]))
        self.assertEqual(len(tenfit.md), len(dat[..., 0]))

    def test_sym_diff_reg(self):

        dat = nib.load(self.img1).get_data()
        aff = nib.load(self.img1).affine
        bval, bvec = read_bvals_bvecs(self.fbval, self.fbvec)
        a, b, tenfit = dtfunc.fit_dti(dat, bval, bvec)
        fa = tenfit.fa
        dat2 = nib.load(self.template).get_data()
        aff2 = nib.load(self.template).affine

        warp, mapping = dtfunc.sym_diff_registration(fa, dat2, aff, aff2)

        self.assertEqual(dat.shape, warp.shape)
        self.assertEqual(mapping.transform_inverse(dat).shape, dat2.shape)

    def test_segment_tissue(self):

        dat = nib.load(self.img1).get_data()
        seg = dtfunc.segment_tissue(dat[..., 0])

        self.assertEqual(len(seg.shape), len(dat.shape))  # both should be 4 dimensional

    def test_roi_stats(self):

        dat = nib.load(self.img1).get_data()
        aff = nib.load(self.img1).affine
        labels = nib.load(self.template_labels).get_data()
        zooms = nib.load(self.img1).header.get_zooms()
        lookup = np.load(self.labels_lookup).item()
        bval, bvec = read_bvals_bvecs(self.fbval, self.fbvec)
        a, b, tenfit = dtfunc.fit_dti(dat, bval, bvec)
        fa = tenfit.fa
        fa[fa < 0.2] = 0
        warp, mapping = dtfunc.sym_diff_registration(fa, labels, aff, aff)
        stats = dtfunc.roi_stats(fa, warp, lookup, zooms)

        for stat in stats:
            self.assertIsNotNone(stat)


if __name__ == "__main__":
    unittest.main()
