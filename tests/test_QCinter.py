import unittest

from pijp_dti import QCinter


IMG_PATH = '/m/InProcess/External/NRC/pijp_dti/NRC-FRA018-0022-V0-a1201/2Register/NRC-FRA018-0022-V0-a1201_b0.nii.gz'
MSK_PATH = '/m/InProcess/External/NRC/pijp_dti/NRC-FRA018-0022-V0-a1201/3Mask/NRC-FRA018-0022-V0-a1201_final_mask.nii.gz'
AUTO_PATH = '/m/InProcess/External/NRC/pijp_dti/NRC-FRA018-0022-V0-a1201/3Mask/NRC-FRA018-0022-V0-a1201_auto_mask.nii.gz'
CODE = 'NRC-FRA018-0022-V0-a1201'


class Test(unittest.TestCase):

    def test_qc_tool(self):
        QCinter.run_qc_interface(CODE, IMG_PATH, AUTO_PATH, MSK_PATH, mosaic_mode=True)


if __name__ == "__main__":
    unittest.main()
