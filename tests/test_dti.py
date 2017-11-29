import unittest

import matplotlib.pyplot as plt
import nibabel as nib
import numpy as np


class Test(unittest.TestCase):

    def test_MaskQC(self):

        og = nib.load('/home/vhasfcellisr/Ryan/test_dti/subjects/t5/stage/t5.nii.gz')
        mask = nib.load('/home/vhasfcellisr/Ryan/test_dti/subjects/t5/prereg/t5_prereg.nii.gz')
        og = og.get_data()
        mask = mask.get_data()
        mask = np.where(mask > 0, 0, 1)
        fig, ax = plt.subplots(3, 3)

        for i in range(0, 3):
            ax[0, i].imshow(og[:, :, og.shape[2]//4, i], cmap='nipy_spectral')
            ax[0, i].imshow(mask[:, :, mask.shape[2]//4, i], cmap='binary_r', alpha=0.5)
            ax[1, i].imshow(og[:, :, og.shape[2]//2, i], cmap='nipy_spectral')
            ax[1, i].imshow(mask[:, :, mask.shape[2]//2, i], cmap='binary_r', alpha=0.5)
            ax[2, i].imshow(og[:, :, og.shape[2]*3//4, i], cmap='nipy_spectral')
            ax[2, i].imshow(mask[:, :, mask.shape[2]*3//4, i], cmap='binary_r', alpha=0.5)

        plt.show()
