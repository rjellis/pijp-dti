import unittest

from pijp_dti import QCinter


IMG_PATH = '/m/InProcess/External/NRC/pijp_dti/NRC-FRA018-0022-V0-a1201/4Tenfit/NRC-FRA018-0022-V0-a1201_fa.nii.gz'
MSK_PATH = '/m/InProcess/External/NRC/pijp_dti/NRC-FRA018-0022-V0-a1201/6Segment/NRC-FRA018-0022-V0' \
           '-a1201_warped_wm_labels' \
           '.nii' \
           '.gz'
AUTO_PATH = '/m/InProcess/External/NRC/pijp_dti/NRC-FRA018-0022-V0-a1201/6Segment/NRC-FRA018-0022-V0' \
            '-a1201_warped_wm_labels' \
            '.nii' \
            '.gz'

CODE = 'NRC-FRA018-0022-V0-a1201'


class Test(unittest.TestCase):

    def test_qc_tool(self):
        QCinter.run_qc_interface(CODE, IMG_PATH, AUTO_PATH, MSK_PATH, mosaic_mode=True)


if __name__ == "__main__":
    unittest.main()
