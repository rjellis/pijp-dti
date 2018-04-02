import os
import subprocess

import nibabel as nib
import numpy as np
from pijp import util

from pijp_nnicv import nifti_io


def load_image(image_path):
    """Loads the nibabel image and prepares it for matplotlib plotting"""
    image_dat = nib.load(image_path).get_data()
    image_dat = nifti_io.rescale(image_dat)
    image_dat = np.stack((image_dat, image_dat, image_dat), axis=-1)

    return np.rot90(image_dat, 1)


def load_overlay(overlay_path):

    overlay_dat = nib.load(overlay_path).get_data()
    return np.rot90(overlay_dat, 1)


def mask_image(image, mask, hue, alpha=1):
    """
    overlay a binary mask on an image
    Args:
        image (ndarray):
        mask (ndarray): boolean or binary array to overlay on img
        hue (list or tuple or ndarray shape [3]): RBG 3-vector
        alpha (float): alpha level of overlay
    Returns:
        img (ndarray): masked img
    """
    factor = np.multiply(hue, alpha)
    img = image.copy()
    img[mask.astype('bool'), ..., 0] = (1 - alpha) * img[mask.astype('bool'), ..., 0] + factor[0]
    img[mask.astype('bool'), ..., 1] = (1 - alpha) * img[mask.astype('bool'), ..., 1] + factor[1]
    img[mask.astype('bool'), ..., 2] = (1 - alpha) * img[mask.astype('bool'), ..., 2] + factor[2]
    return img


def masks_are_same(auto_mask, final_mask):
    auto_mask_dat = nib.load(auto_mask).get_data()
    final_mask_dat = nib.load(final_mask).get_data()

    return np.array_equal(auto_mask_dat, final_mask_dat)


def get_mask_editor():
    mask_editor = os.path.join(util.configuration['fsl']['path'], 'fsleyes')
    if not os.path.exists(mask_editor):
        raise FileNotFoundError
    return mask_editor


def open_editor(img, overlay):
    editor = get_mask_editor()
    cmd = "{mask_editor} -xh -yh {img} {overlay} -a 40 -cm Red".format(mask_editor=editor, img=img,
                                                                       overlay=overlay)
    args = cmd.split()

    return subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
