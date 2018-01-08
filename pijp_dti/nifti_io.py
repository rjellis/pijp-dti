import numpy as np
import nibabel as nib
import scipy.ndimage as ndimage


def pad_feat(feat, p=33):
    """
    pads a 5D array (batch,x,y,z,channels) with <p> zeros on both sides of x,y,z dimensions
    Args:
        feat (ndarray): 5D array to be padded
        p (int): size of padding
    Returns:
        ndarray : array with zero-padded spacial dimensions
    """
    paddings = [[0, 0], [p, p], [p, p], [p, p], [0, 0]]
    return np.pad(feat, paddings, 'constant')


def unpad(arr, p=33):
    """
    removes padding of size <p> from spacial dimension of 5D array (batch,x,y,z,channels)
    Args:
        arr (ndarray):
        p (int):
    Returns:
        ndarray : arr with p voxels removed from both sides of each spacial dimension
    """
    return arr[:, p:-p, p:-p, p:-p, :]


def shrink(mask):
    """
    return three (x,y,z)  slice objects for smallest bounding box around
    largest connected component in a 3D array
    Args:
        mask (ndarray): binary 3D array
    Returns:
        tuple : 3-tuple of slice objects for indexing input
    """

    label_im, nb_labels = ndimage.label(mask)

    # Find the largest connected component
    sizes = ndimage.sum(mask, label_im, range(nb_labels + 1))
    mask_size = sizes < np.max(sizes)
    remove_pixel = mask_size[label_im]
    label_im[remove_pixel] = 0
    labels = np.unique(label_im)
    label_im = np.searchsorted(labels, label_im)

    # Now that we have only one connected component, extract it's bounding box
    slice_x, slice_y, slice_z = ndimage.find_objects(label_im != 0)[0]
    return slice_x, slice_y, slice_z


def load_nii_RASplus(path):
    """
    loads a nifti image in RAS+ coordinate system. (Right, Anterior, Superior is positive octant)
    Args:
        path (str): path to nifti file.
    Returns:
        tuple : 2-tuple containing (ndarray with image data, ndarray with affine matrix)
    """
    img = nib.load(path)
    img = nib.as_closest_canonical(img)
    array = np.asarray(img.dataobj)
    return array, img.affine


def load_nii(path):
    """
    loads a nifti image in whatever coordinate system its saved in
    Args:
        path (str): path to nifti file.
    Returns:
        tuple : 2-tuple containing (ndarray with image data, ndarray with affine matrix)
    """
    img = nib.load(path)
    array = np.asarray(img.dataobj)
    return array, img.affine

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


def binarize(mask):
    """
    takes a probabilistic array and turns it into a binary array.
    assumes values are between 0 and 1. Do not use otherwise.
    Args:
        mask (ndarray): array of floats between 0 and 1
    Returns:
        ndarray : binary version of input
    """
    mask[mask > 0.5] = 1
    mask[mask <= 0.5] = 0
    return mask.astype('float')


def save_as_nifti(outpath, data, affine):
    """
    creates a nifti file given data and affine
    Args:
        outpath (str): where to save nifti file
        data (ndarray): image data for file
        affine (ndarray): 4x4 affine transformation matrix for data
    """
    nib.Nifti1Image(np.squeeze(data), affine=affine).to_filename(outpath)


def extract_largest_component(array):
    """
    extracts the largest contiguous object in a binary image
    Args:
        array (ndarray): binary array
    Returns:
        ndarray : same array with all but largest object removed
    """
    bin_arr = binarize(array)
    s = ndimage.generate_binary_structure(3, 1)  # define contiguous voxels
    labeled_array, numpatches = ndimage.label(bin_arr, s)
    sizes = ndimage.sum(bin_arr, labeled_array, range(1, numpatches + 1))
    map = np.where(sizes == sizes.max())[0] + 1
    max_index = np.zeros(numpatches + 1, np.uint8)
    max_index[map] = 1
    max_feature = max_index[labeled_array]
    max_feature = max_feature.astype('int')
    return array * max_feature


def fill_holes(array):
    array = binarize(array).astype('int')
    arr = ndimage.binary_fill_holes(array).astype('int').astype('float')
    return arr
