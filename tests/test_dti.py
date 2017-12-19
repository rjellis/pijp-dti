import unittest
from pijp_dti import QCinter, dtiQC


class Test(unittest.TestCase):

    def test_MaskQC(self):

        denoised = '/m/InProcess/External/NRC/dti/NRC-FRA018-0003-V0-a1001/prereg/NRC-FRA018-0003-V0-a1001_denoised' \
                   '.nii.gz'
        auto_mask = '/m/InProcess/External/NRC/dti/NRC-FRA018-0003-V0-a1001/prereg/NRC-FRA018-0003-V0-a1001_auto_mask' \
                    '.nii.gz'
        code = 'NRC-FRA018-0003-V0-a1001'

        mask_fig = dtiQC.get_mask_mosaic(denoised, auto_mask)

        QCinter.qc_tool(mask_fig, code)

    def test_WarpQC(self):

        fa = '/m/InProcess/External/NRC/dti/NRC-FRA018-0003-V0-a1001/tenfit/NRC-FRA018-0003-V0-a1001_fa.nii.gz'
        label = '/m/InProcess/External/NRC/dti/NRC-FRA018-0003-V0-a1001/tenfit/NRC-FRA018-0003-V0-a1001_warped_labels.nii.gz'
        code = 'NRC-FRA018-0003-V0-a1001'

        warp_fig = dtiQC.get_warp_mosaic(fa, label, alpha=0.2)
        QCinter.qc_tool(warp_fig, code)
