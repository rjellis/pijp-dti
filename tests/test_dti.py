import unittest
import os

import matplotlib.pyplot as plt
import nibabel as nib
import numpy as np
from dipy.segment.mask import applymask

from pijp_dti import dtfunc
from pijp_dti import animate

class Test(unittest.TestCase):

    def test_MaskQC(self):

        og = nib.load('/home/vhasfcellisr/Ryan/t1_dti/subjects/test2/stage/test2.nii.gz').get_data()
        mask = dtfunc.mask(og)

        masked = animate.mask_image(og, mask, hue = 0, alpha=0.9)
        mov = animate.Nifti_Animator(masked)
        mov.cmap = "hot"
        mov.interval = 10
        mov.plot(show=False)
        mov.save('/home/vhasfcellisr/Ryan/mov2.mp4')
        print("Saved")
