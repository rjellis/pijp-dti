import unittest

from pijp_dti import QCinter

CODE = 'NRC-FRA018-0003-V0-a1001'
IMG_PATH = '/m/InProcess/External/NRC/pijp_dti/{code}/2Register/{code}_b0.nii.gz'.format(code=CODE)
MSK_PATH = '/m/InProcess/External/NRC/pijp_dti/{code}/3Mask/{code}_final_mask.nii.gz'.format(code=CODE)
AUTO_PATH = '/m/InProcess/External/NRC/pijp_dti/{code}/3Mask/{code}_auto_mask.nii.gz'.format(code=CODE)

class Test(unittest.TestCase):

    def test_qc_tool(self):
        step = 'MaskQC'
        QCinter.run_qc_interface(CODE, IMG_PATH, AUTO_PATH, MSK_PATH, step)

if __name__ == "__main__":
    unittest.main()
