import os

import numpy as np
import matplotlib.pyplot as plt
from matplotlib import animation


class Nifti_Animator(object):

    def __init__(self, img):
        self.img = img
        self.interval = 50
        self.ani = None

    def plot(self, show=True):

        fig = plt.figure()
        ax = fig.add_subplot(111)
        ims = []

        for i in range(0, self.img.shape[2]):
            im = plt.imshow(self.img[:, :, i, :], animated=True, interpolation=None)
            t = ax.annotate("Slice {}".format(i+1), (0, 0), (0, -1))
            ims.append([im, t])

        self.ani = animation.ArtistAnimation(fig, ims, repeat=True, interval=self.interval)

        if show:
            plt.axis("off")
            plt.show()

class Mosaic(object):

    def __init__(self, img):
        self.img = img
        self.fig = None

    def plot(self, show=True, save=False, path=None):

        slc = self.img.shape[2]
        subplot_size = int(np.sqrt(self._get_next_square(slc)))
        fig, ax = plt.subplots(subplot_size, subplot_size)

        slc_idx = 0

        for i in range(0, subplot_size):
            for j in range(0, subplot_size):
                if slc_idx < slc:
                    ax[i, j].imshow(self.img[:, :, slc_idx, 0], interpolation=None)
                    ax[i, j].imshow(self.img[:, :, slc_idx, 1], interpolation=None)
                    ax[i, j].imshow(self.img[:, :, slc_idx, 2], interpolation=None)

                ax[i, j].axis("off")
                slc_idx += 1

        if show:
            plt.subplots_adjust(wspace=0, hspace=0)
            plt.show()

        if save:
            plt.savefig(path)



    def _get_next_square(self, num):
        sq = num
        while np.mod(np.sqrt(sq), 1) != 0:
            sq = (sq // 1) + 1
        return sq



def mask_image(img, mask, hue, alpha=1):
    """
    overlay a binary mask on an image
    Args:
        img (ndarray):
        mask (ndarray): boolean or binary array to overlay on img
        hue (list or tuple or ndarray shape [3]): RBG 3-vector
        alpha (float): alpha level of overlay
    Returns:
        ndarray : masked img
    """
    factor = np.multiply(hue, alpha)
    img[mask.astype('bool'), ..., 0] = (1 - alpha) * img[mask.astype('bool'), ..., 0] + factor[0]
    img[mask.astype('bool'), ..., 1] = (1 - alpha) * img[mask.astype('bool'), ..., 1] + factor[1]
    img[mask.astype('bool'), ..., 2] = (1 - alpha) * img[mask.astype('bool'), ..., 2] + factor[2]
    return img

def rescale(array, bins=1000):
    """
    Normalizes array by integrating histogram.
    Finds the value at which the area under the curve is approximately %98.5 of total area.
    Saturates at that value. assumes all values in array > 0
    Args:
        array (ndarray): array to be normalized
        bins (int): number of bins to use in histogram. corresponds to precision of integration
    Returns:
        ndarray : normalized array
    """
    h, bin_edges = np.histogram(array, bins=1000)
    bin_width = (bin_edges[1] - bin_edges[0])
    h_area = np.sum(h)
    idcs = []
    for i in range(len(h)):
        i = i + 1
        val = np.sum(h[:-i]) / h_area
        if val > 0.98:
            idcs.append((i, val))
        else:
            break
    idcs.sort(key=lambda x: (abs(0.985 - x[1]), 1 / x[0]))
    idx = idcs[0][0]
    maxval = max(array[array < bin_edges[-idx]])
    array[array > maxval] = maxval
    return array / maxval

def unmask_image(img, orig, mask):
    """
    replace values of one array with corresponding values of another array, indexed by a third array
    Args:
        img (ndarray): image to be modified
        orig (ndarray): image with values to replace ones in img
        mask (ndarray): boolean or binary array specifying which values to replace
    Returns:
        ndarray : modified img
    """
    img[mask.astype('bool'), :] = orig[mask.astype('bool'), :]
    return img


