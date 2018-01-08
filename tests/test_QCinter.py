import unittest

from pijp_dti import QCinter, mosaic


IMG_PATH = '/home/vhasfcellisr/test_case/2Register/NRC-FRA018-0005-V0-a1001_b0.nii.gz'
MSK_PATH = '/home/vhasfcellisr/test_case/3Mask/NRC-FRA018-0005-V0-a1001_auto_mask.nii.gz'
CODE = 'NRC-FRA018-0005-V0-a1001'

class Test(unittest.TestCase):

    def test_qc_tool(self):
        fig = mosaic.get_mask_mosaic(IMG_PATH, MSK_PATH)
        QCinter.run_qc_interface(fig, CODE)


if __name__ == "__main__":
    unittest.main()
