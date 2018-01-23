import numpy as np
import nibabel as nib
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from pijp_dti.nifti_io import rescale


class Mosaic(object):

    def __init__(self, img):
        self.img = img
        plt.close('all')  # Close all other plots before making a new one

    def plot(self, mosaic_path=None):

        slc = self.img.shape[2]
        subplot_size = int(np.sqrt(get_prev_square(slc)))

        fig, ax = plt.subplots(subplot_size, subplot_size)
        fig.set_facecolor('black')

        slc_idx = 0
        for i in range(0, subplot_size):
            for j in range(0, subplot_size):
                if slc_idx < slc:
                    ax[i, j].imshow(np.rot90(self.img[:, :, slc_idx, :], 1), interpolation=None)

                ax[i, j].axis("off")
                slc_idx += 1

        plt.subplots_adjust(left=0.01, bottom=0.01, right=0.99, top=0.99,
                            wspace=0, hspace=0)
        if mosaic_path is not None:
            plt.savefig(mosaic_path, facecolor='black', edgecolor='black', format='png')

        return fig

    def animate(self):

        fig = plt.figure()
        ax = fig.add_subplot(111)
        ax.axis('off')
        ims = []
        fig.set_facecolor('black')
        for i in range(0, self.img.shape[2]):

            im = plt.imshow(np.rot90(self.img[:, :, i, :], 1), animated=True, interpolation=None)
            t = ax.annotate("Slice {}".format(i+1), (0, 0), (0, -1))
            ims.append([im, t])
        return fig, ims

    def plot_one_slice_with_overlay(self, overlay, alpha=1.0, cmap_img='gray',
                                    cmap_overlay='nipy_spectral', mosaic_path=None):
        fig = plt.figure()
        fig.set_facecolor('black')
        plt.axes(frameon=False)
        plt.imshow(np.rot90(self.img[:, :, self.img.shape[2]//2], 1), cmap=cmap_img, interpolation=None)
        plt.imshow(np.rot90(overlay[:, :, overlay.shape[2] // 2], 1), cmap=cmap_overlay, interpolation=None,
                   alpha=alpha)

        if mosaic_path is not None:
            plt.savefig(mosaic_path, facecolor='black', edgecolor='black', format='png')

        return fig


def get_prev_square(num):
    sq = num
    while np.mod(np.sqrt(sq), 1) != 0:
        sq = (sq // 1) - 1
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


def get_mask_mosaic(image_path, mask_path, mosaic_path=None):
    image = nib.load(image_path).get_data()
    mask = nib.load(mask_path).get_data()
    image = rescale(image)
    image = np.stack((image, image, image), axis=-1)
    masked = mask_image(image, mask, hue=[1, 0, 0], alpha=0.5)
    return Mosaic(masked).plot(mosaic_path)


def get_seg_mosaic(image_path, seg_path, mosaic_path=None):
    image = nib.load(image_path).get_data()
    seg = nib.load(seg_path).get_data()
    image = rescale(image)
    image = np.stack((image, image, image), axis=-1)
    masked = mask_image(image, seg, hue=[1, 0, 0], alpha=0.5)
    return Mosaic(masked).plot(mosaic_path)


def get_warp_mosaic(image_path, label_path, mosaic_path=None, alpha=0.2):
    image = nib.load(image_path).get_data()
    label = nib.load(label_path).get_data()
    return Mosaic(image).plot_one_slice_with_overlay(label, alpha=alpha, mosaic_path=mosaic_path)


def get_animation(image_path, mask_path):
    image = nib.load(image_path).get_data()
    mask = nib.load(mask_path).get_data()
    image = rescale(image)
    image = np.stack((image, image, image), axis=-1)
    masked = mask_image(image, mask, hue=[1, 0, 0], alpha=0.5)
    return Mosaic(masked).animate()
