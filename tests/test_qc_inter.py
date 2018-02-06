import unittest

from pijp_dti import qc_inter

CODE = 'SampleCode'
IMG_PATH = 'Sample/Path/To/Image'
MSK_PATH = 'Sample/Path/To/Mask'
AUTO_PATH = 'Sample/Path/To/AutoMask'

class Test(unittest.TestCase):

    def test_qc_inter(self):
        step = 'MaskQC'
        print(qc_inter.run(CODE, IMG_PATH, AUTO_PATH, MSK_PATH, step))

if __name__ == "__main__":
    unittest.main()
