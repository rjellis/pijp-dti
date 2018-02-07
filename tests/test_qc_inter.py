import unittest

from pijp_dti import qc_inter

CODE = 'NRC-FRA018-0003-V0'
IMG_PATH = '/m/InProcess/External/NRC/pijp-dti-dev/{code}/2Register/{code}_b0.nii.gz'.format(code=CODE)
MSK_PATH = '/m/InProcess/External/NRC/pijp-dti-dev/{code}/3Mask/{code}_final_maks.nii.gz'.format(code=CODE)
AUTO_PATH = '/m/InProcess/External/NRC/pijp-dti-dev/{code}/3Mask/{code}_auto_mask.nii.gz'.format(code=CODE)

class Test(unittest.TestCase):

    def test_qc_inter(self):
        step = 'MaskQC'
        print(qc_inter.run(CODE, IMG_PATH, AUTO_PATH, MSK_PATH, step))

if __name__ == "__main__":
    unittest.main()
