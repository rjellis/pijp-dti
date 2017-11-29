import unittest
from pijp_dti import dti

class Test(unittest.TestCase):

    def test_MaskQC(self):

        qc = dti.MaskQC(None, None, None)
        qc.fdwi = '/home/vhasfcellisr/Ryan/test_dti/subjects/t1/stage/t1.nii.gz'
        qc.prereg = '/home/vhasfcelilsr/Ryan/test_dti/subjects/t1/prereg/t1_prereg.nii.gz'

        qc.run()
