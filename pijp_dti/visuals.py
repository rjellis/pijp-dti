import os

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation

pardir = os.path.dirname(__file__)

class Nifti_Animator(object):

    def __init__(self, img):
        self.img = img
        self.cmap = 'gray'
        self.interval = 50
        self.ani = None

    def plot(self, show=True):

        fig = plt.figure()
        ax = fig.add_subplot(111)
        ims = []

        for i in range(0, self.img.shape[2]):
            im = plt.imshow(self.img[:, :, i].T, cmap=self.cmap, animated=True, interpolation=None)
            t = ax.annotate("Slice {}".format(i+1), (0, 0), (0, -1))
            ims.append([im, t])

        self.ani = animation.ArtistAnimation(fig, ims, repeat=True, interval=self.interval)

        if show:
            plt.axis("off")
            plt.show()


class Mosaic(object):

    def __init__(self, img):
        self.img = img
        self.cmap = 'gray'
        self.fig = None

    def plot(self, show=True, save=False, path=None):

        slc = self.img.shape[2]
        subplot_size = int(np.sqrt(self._get_next_square(slc)))
        fig, ax = plt.subplots(subplot_size, subplot_size)

        slc_idx = 0

        for i in range(0, subplot_size):
            for j in range(0, subplot_size):
                if slc_idx < slc:
                    ax[i, j].imshow(self.img[:, :, slc_idx].T, cmap=self.cmap, interpolation=None)
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


def mask_image(img, mask, hue=0, alpha=1):
    """
    overlay a binary mask on an image
    Args:
        img (ndarray):
        mask (ndarray): boolean or binary array to overlay on img
        hue (int): scale the intensity
        alpha (float): alpha level of overlay

    Returns:
        ndarray : masked img
    """
    factor = hue*alpha
    img[mask.astype('bool')] = (1 - alpha) * img[mask.astype('bool')] + factor

    return img
