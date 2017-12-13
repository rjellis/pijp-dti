import unittest
from pijp_dti import dtiQC

class Test(unittest.TestCase):

    def test_MaskQC(self):
        img = '/m/InProcess/External/NRC/dti/NRC-FRA018-0005-V0-a1001/prereg/NRC-FRA018-0005-V0-a1001_denoised.nii.gz'
        msk = '/m/InProcess/External/NRC/dti/NRC-FRA018-0005-V0-a1001/prereg/NRC-FRA018-0005-V0-a1001_binary_mask.npy'
        code = 'NRC-FRA018-0005-V0-a1001'
        dtiQC.run_mask_qc(img, msk, code)
