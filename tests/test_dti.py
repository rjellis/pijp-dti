import unittest

import matplotlib.pyplot as plt
import nibabel as nib
import numpy as np

from dipy.segment.mask import applymask

from pijp_dti import dtfunc
from pijp_dti import animate

class Test(unittest.TestCase):

    def test_preregister(self):

        dat = nib.load('/home/vhasfcellisr/Ryan/test/t2/test2.nii.gz').get_data()
        denoised = dtfunc.denoise(dat)
        masked = dtfunc.mask(denoised)
        comp = animate.mask_image(denoised, masked)
        a = animate.Nifti_Animator(comp)
        a.interval = 200
        a.plot()

