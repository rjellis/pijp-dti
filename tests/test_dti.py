import unittest
from pijp_dti import QCinter, dtiQC


class Test(unittest.TestCase):

    def test_WarpQC(self):

        fa = '/m/InProcess/External/NRC/dti/NRC-FRA018-0003-V0-a1001/tenfit/NRC-FRA018-0003-V0-a1001_fa.nii.gz'
        label = '/m/InProcess/External/NRC/dti/NRC-FRA018-0003-V0-a1001/warp/NRC-FRA018-0003-V0-a1001_warped_labels' \
                '.nii.gz'
        code = 'NRC-FRA018-0003-V0-a1001'

        warp_fig = dtiQC.get_warp_mosaic(fa, label, alpha=0.1)
        result, comment = QCinter.qc_tool(warp_fig, code)
        print(result)
