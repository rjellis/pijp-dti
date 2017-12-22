import numpy as np
import nibabel as nib
import matplotlib.pyplot as plt


class Mosaic(object):

    def __init__(self, img):
        self.img = img

    def plot(self, mosaic_path=None):

        slc = self.img.shape[2]
        subplot_size = int(np.sqrt(get_next_square(slc)))

        fig, ax = plt.subplots(subplot_size, subplot_size)
        plt.subplots_adjust(left=0.01, bottom=0.01, right=0.99, top=0.99,
                            wspace=0, hspace=0)

        slc_idx = 0

        for i in range(0, subplot_size):
            for j in range(0, subplot_size):
                if slc_idx < slc:
                    ax[i, j].imshow(np.rot90(self.img[:, :, slc_idx, 0], 1), interpolation=None)
                    ax[i, j].imshow(np.rot90(self.img[:, :, slc_idx, 1], 1), interpolation=None)
                    ax[i, j].imshow(np.rot90(self.img[:, :, slc_idx, 2], 1), interpolation=None)

                ax[i, j].axis("off")
                slc_idx += 1

        fig.set_facecolor('black')

        if mosaic_path is not None:
            plt.savefig(mosaic_path, facecolor='black', edgecolor='black', format='png')

        return fig

    def two_plot(self, img2, alpha=1.0, mosaic_path=None, factor=4):

        fig = plt.figure()
        fig.set_facecolor('black')
        plt.axes(frameon=False)
        plt.imshow(np.rot90(self.img[:, :, self.img.shape[2]//2], 1), cmap='gray', interpolation=None)
        plt.imshow(np.rot90(img2[:, :,  img2.shape[2]//2], 1), cmap='nipy_spectral', interpolation=None, alpha=alpha)

        if mosaic_path is not None:
            plt.savefig(mosaic_path, facecolor='black', edgecolor='black', format='png')

        return fig


def get_next_square(num):
    sq = num
    while np.mod(np.sqrt(sq), 1) != 0:
        sq = (sq // 1) + 1
    return sq


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
    h, bin_edges = np.histogram(array, bins)
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


def get_warp_mosaic(image_path, label_path, mosaic_path=None, alpha=0.2):
    image = nib.load(image_path).get_data()
    label = nib.load(label_path).get_data()

    return Mosaic(image).two_plot(label, alpha=alpha, mosaic_path=mosaic_path)
