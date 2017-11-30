import matplotlib.pyplot as plt
import matplotlib.animation as animation
import nibabel as nib
import numpy as np


class Nifti_Animator(object):

    def __init__(self, img):
        self.img = img
        self.cmap = 'gray'
        self.interval = 50

    def plot(self, show=True):

        fig = plt.figure()
        ax = fig.add_subplot(111)
        ims = []


        for i in range (0, self.img.shape[-1]):
            if len(self.img.shape) > 3:
                for j in range(0, self.img.shape[2]):
                    im = plt.imshow(self.img[:, :, j, i].T, cmap=self.cmap, animated=True, interpolation=None)
                    t = ax.annotate("Direction {}".format(i+1), (0, 0), (0, -1))
                    ims.append([im, t])
            else:
                im = plt.imshow(self.img[:, :, i].T, cmap=self.cmap, animated=True, interpolation=None)
                ims.append([im])

        self.ani = animation.ArtistAnimation(fig, ims, repeat=True, interval=self.interval)

        if show:
            plt.axis("off")
            plt.show()


def mask_image(img, mask, hue=255, alpha=1):
    """
    overlay a binary mask on an image
    Args:
        img (ndarray):
        mask (ndarray): boolean or binary array to overlay on img
        alpha (float): alpha level of overlay

    Returns:
        ndarray : masked img
    """
    factor = hue*alpha
    img[mask.astype('bool')] = (1 - alpha) * img[mask.astype('bool')] + factor

    return img