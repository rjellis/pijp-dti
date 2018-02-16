import unittest

from pijp_dti import qc_inter

CODE = 'NRC-FRA018-0003-V0'
IMAGE_PATH = '/m/InProcess/External/NRC/pijp-dti-dev/NRC-FRA018-0003-V0-a1001/2Register/NRC-FRA018-0003-V0-a1001_b0.nii.gz'
OVERLAY_PATH = '/m/InProcess/External/NRC/pijp-dti-dev/NRC-FRA018-0003-V0-a1001/3Mask/NRC-FRA018-0003-V0-a1001_final_mask.nii.gz'

class Test(unittest.TestCase):

    def test_qc_inter(self):
        step = 'MaskQC'
        print(qc_inter.run(CODE, IMAGE_PATH, OVERLAY_PATH, OVERLAY_PATH, step))

if __name__ == "__main__":
    unittest.main()
