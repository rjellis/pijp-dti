import unittest
import os

import matplotlib.pyplot as plt
import nibabel as nib
import numpy as np
from dipy.segment.mask import applymask

from pijp_dti import dtfunc
from pijp_dti import dtiQC

class Test(unittest.TestCase):

    def test_MaskQC(self):
        og = nib.load('/home/vhasfcellisr/Ryan/t1_dti/subjects/test2/stage/test2.nii.gz').get_data()
        mask = dtfunc.mask(og)

        og = dtiQC.rescale(og)
        og = np.stack((og, og, og), axis=-1)
        masked = dtiQC.mask_image(og, mask, hue = [0, 1, 0], alpha=0.5)
        mos = dtiQC.Mosaic(masked)
        mos.plot(show=True, save=False, path= '/home/vhasfcellisr/test.png')
