import unittest
import os
import subprocess

from pijp import util
from pijp_dti import QCinter, mosaic


IMG_PATH = '/m/InProcess/External/NRC/pijp_dti/NRC-FRA018-0022-V0-a1201/2Register/NRC-FRA018-0022-V0-a1201_b0.nii.gz'
MSK_PATH = '/m/InProcess/External/NRC/pijp_dti/NRC-FRA018-0022-V0-a1201/3Mask/NRC-FRA018-0022-V0-a1201_auto_mask.nii.gz'
CODE = 'NRC-FRA018-0005-V0-a1001'


class Test(unittest.TestCase):

    def test_qc_tool(self):
        fig = mosaic.get_mask_mosaic(IMG_PATH, MSK_PATH)
        QCinter.run_qc_interface(fig, CODE, edit_cmd=open_mask_editor)


if __name__ == "__main__":
    unittest.main()


def open_mask_editor():
        mask_editor = get_mask_editor()
        cmd = "{mask_editor} -m single {img} {overlay} -t 0.5 -l Red".format(mask_editor=mask_editor, img=IMG_PATH,
                                                                             overlay=MSK_PATH)
        run_cmd(cmd)


def get_mask_editor():
    mask_editor = util.configuration['fslview']
    if not os.path.exists(mask_editor):
        raise Exception("fslview not found")
    return mask_editor


def run_cmd(cmd):
    args = cmd.split()
    subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
