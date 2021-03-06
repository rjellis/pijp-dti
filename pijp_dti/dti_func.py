import numpy as np
from dipy.align import (imaffine, imwarp, transforms, metrics)
from dipy.core import gradients
from dipy.denoise import noise_estimate, non_local_means
from dipy.denoise.localpca import localpca
from dipy.denoise.pca_noise_estimate import pca_noise_estimate
from dipy.reconst import dti
from dipy.segment import mask as otsu
from dipy.segment.tissue import TissueClassifierHMRF

from pijp_nnicv.nifti_io import fill_holes, extract_largest_component, rescale


def mask(dat):
    """Skull strip using the Median Otsu method.

    median_radius is the radius (in voxels) for the median filter
    num_pass is the number of passes for the median filter

    Args:
        dat (ndarray): 3D image.

    Returns:
        bin_mask (ndarray): The skull stripped image.

    """

    rescaled_dat = rescale(dat)
    mask_dat, bin_dat = otsu.median_otsu(
        rescaled_dat, median_radius=2, numpass=4, dilate=2)
    bin_mask = fill_holes(bin_dat)
    bin_mask = extract_largest_component(bin_mask)

    return bin_mask


def apply_mask(dat, bin_mask):
    """Apply the binary mask.

    Args:
        dat (ndarray): The image to be masked.
        bin_mask (ndarray): boolean mask.

    Returns:
        masked (ndarray): The image with the mask applied.

    """
    return otsu.applymask(dat, bin_mask)


def denoise(dat):
    """Denoise a data set using Non Local Means.

    Args:
        dat (ndarray): 3D or 4D image.

    Returns:
        denoise_dat (ndarray): denoised image.

    """
    sigma = noise_estimate.estimate_sigma(dat)
    denoise_dat = []

    if len(dat.shape) == 4:
        for i in range(0, dat.shape[3]):
            denoise_dat.append(
                non_local_means.non_local_means(dat[..., i], sigma[i]))

        denoise_dat = np.stack(denoise_dat, axis=-1)

    elif len(dat.shape) == 3:
        denoise_dat = non_local_means.non_local_means(dat, sigma)

    return denoise_dat


def denoise_pca(dat, bval, bvec):
    """Denoise a data set using Local PCA.

    Local PCA is a denoising method specific to 4D diffusion weighted images.

    Args:
        dat (ndarray): 3D or 4D image.
        bval (ndarray): 1D ndarray containing the b-values
        bvec (ndarray): 2D ndarray containing the b-vectors

    Returns:
        denoise_dat (ndarray): The denoised ndarray

    """
    gtab = gradients.gradient_table(bval, bvec)
    sigma = pca_noise_estimate(dat, gtab)
    denoise_dat = localpca(dat, sigma=sigma)
    return denoise_dat


def average_b0(dat, aff, bval):
    """Obtain the average b0 image from a 4D DWI image.

    Args:
        dat (ndarray): 4D diffusion weighted image.
        aff (ndarray): 4 X 4 affine of the image.
        bval (ndarray): 1D ndarray containing the b-values

    Returns:
        b0 (ndarray): 3D averaged b0 image.

    """
    b0 = None
    b0s_reg = []

    for i in range(0, len(bval)):
        if bval[i] == 0:
            if b0 is None:
                b0 = dat[..., i]
            b0_reg, b0_aff, b0_map = affine_registration(
                b0, dat[..., i], aff, aff, rigid=True)
            b0s_reg.append(b0_reg)

    b0s_reg = np.stack(b0s_reg, axis=-1)
    b0_avg = np.mean(b0s_reg, axis=-1)

    return b0_avg


def register(b0, dwi, b0_aff, aff, bval, bvec):
    """Rigidly register a 4D DWI to its own 3D b0 image.

    Args:
        b0 (ndarray): 3D average b0 image.
        dwi (ndarray): 4D DWI image
        b0_aff (ndarray): 4 X 4 affine matrix for the b0
        aff (ndarray): 4 X 4 affine matrix for the DWI
        bval (ndarray): 1D ndarray containing the b-values
        bvec (ndarray): 2D ndarray containing the b-vectors

    Returns:
        reg_dat (ndarray): 4D ndarray of the registered DWI
        reg_bvecs (ndarray): 2D ndarray of the updated b-vectors

    """
    affines = []
    reg_map = []
    reg_dat = []

    for i in range(0, dwi.shape[3]):
        reg_dir, reg_aff, reg_map_slice = affine_registration(
            b0, dwi[..., i], b0_aff, aff, rigid=True)
        reg_dat.append(reg_dir)
        reg_map.append(reg_map_slice.affine)
        if bval[i] != 0: # Only want to update b-vectors with non-zero b-values
            affines.append(reg_aff)

    reg_dat = np.stack(reg_dat, axis=-1)
    reg_map = np.stack(reg_map, axis=-1)
    gtab = gradients.gradient_table(bval, bvec)
    new_gtab = gradients.reorient_bvecs(gtab, affines)
    reg_bvecs = new_gtab.bvecs

    return reg_dat, reg_bvecs, reg_map


def fit_dti(dat, bval, bvec):
    """Fit the tensor using the Weighted Least Squares fit method.

    Args:
        dat (ndarray): 4D diffusion weighted image.
        bval (ndarray): 1D ndarray containing the b-values
        bvec (ndarray): 2D ndarray containing the b-vectors

    Returns:
        evals (ndarray): 4D ndarray of the eigenvalues
        evecs (ndarray): 5D ndarray of the eigenvectors
        tenfit (TensorFit object): TensorFit dipy object

    """
    gtab = gradients.gradient_table(bval, bvec)
    tenmodel = dti.TensorModel(gtab)
    tenfit = tenmodel.fit(dat)
    evals = tenfit.evals
    evecs = tenfit.evecs

    return evals, evecs, tenfit


def segment_tissue(dat):
    """Segments the image into different tissue classifications

    Args:
        dat (ndarray): 3D image

    Returns:
          pve (ndarray): 4D ndarray where the 4th dimension is the tissue class
    """

    nclass = 4
    beta = 0.1

    hmrf = TissueClassifierHMRF()
    hmrf.verbose = False
    initial_seg, final_seg, pve = hmrf.classify(dat, nclass, beta)

    return pve


def apply_tissue_mask(dat, segmented, tissue=1, prob=50):
    """Masks the data using the segmented tissue

    Args:
        dat (ndarray)
        segmented (ndarray)
        tissue (int)
        prob (int)

    Returns:
        masked_tissue (ndarray)
    """
    tissue_mask = segmented[..., tissue]
    threshold = (prob/100)
    dat[tissue_mask < threshold] = 0

    return dat


def roi_stats(dat, overlay, labels, zooms):
    """Get statistics on a diffusion tensor measure in specific roi's

    Args:
        dat (ndarray): 3D image of an diffusion tensor measurement.
        overlay (ndarray): 3D label image.
        labels (Union): A dictionary of overlay values as keys that correspond
                        to region labels_lookup as dictionary values.
        zooms (list): list of voxel dimensions
    Returns:
        stats (list): Array of the list of stats for all regions of interests.

    """
    roi_voxels = dict()
    stats = [['name', 'min', 'max', 'mean', 'sd', 'median', 'volume']]
    vox_size = zooms[0] * zooms[1] * zooms[2]  # The size of voxels in mm
    for roi_labels in labels.values():
        roi_voxels[roi_labels] = []  # A dynamic list for each of the ROI's

    for coord, val in np.ndenumerate(dat):
        key = overlay[coord]  # Get the integer value from the overlay image
        if key in labels:  # Find the label name for that integer value
            roi_name = labels[key]
            if val != 0:
                roi_voxels[roi_name].append(val)

    for rois in roi_voxels.keys():
        npa = np.asarray(roi_voxels[rois])
        try:
            # Name, Min, Max, Mean, Std. Dev, Median, Volume
            stats.append([rois, npa.min(), npa.max(), npa.mean(),
                          npa.std(), np.median(npa), (len(npa)*vox_size)])

        except ValueError:  # Catches rows with empty ROIs
            stats.append([rois, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0])

    return stats


def affine_registration(static, moving,
                        static_affine, moving_affine, rigid=False):
    """Register one 3D array to another using linear registration.

    Args:
        static (ndarray): 3D image used as  reference
        moving (ndarray): 3D image to register
        static_affine (ndarray): 4 X 4 affine matrix of the static image.
        moving_affine (ndarray): 4 X 4 affine matrix of the moving image.
        rigid (bool): A flag for rigid registration

    Returns:

        dat_reg (ndarray): The 3D registered moving image.
        affine (ndarray): 4 X 4 transformation matrix

    """
    # Mutual information Metric
    nbins = 32  # Number of bins for computing the histograms
    sampling_prop = 100  # percentage of voxels (0, 100]
    metric = imaffine.MutualInformationMetric(nbins, sampling_prop)
    level_iters = [10000, 1000, 100]  # coarse to fine
    sigmas = [3.0, 1.0, 0.0]
    factors = [4, 2, 1]  # Factors that determine resolution

    affreg = imaffine.AffineRegistration(
        metric, level_iters=level_iters, sigmas=sigmas,
        factors=factors, verbosity=0)
    params0 = None

    if rigid:
        transform = transforms.RigidTransform3D()
    else:
        transform = transforms.AffineTransform3D()

    # 'mass' tells optimize to align the image's centers of mass
    aff_map = affreg.optimize(static, moving,
                              transform, params0,
                              static_affine, moving_affine, 'mass')
    dat_reg = aff_map.transform(moving)

    return dat_reg, aff_map.affine, aff_map


def sym_diff_registration(static, moving, static_affine, moving_affine):
    """Register one 3D array to another using non-linear registration.

    Args:
        static (ndarray): 3D image used as reference.
        moving (ndarray): 3D image to register
        static_affine (ndarray): 4 X 4 affine matrix of the static image.
        moving_affine (ndarray): 4 X 4 affine matrix of the moving image.

    Returns:
        warped_moving (ndarray): The registered moving 3D image
        mapping (DiffeomorphicMap): The mapping object

    """
    moving_reg, pre_align, reg_map = affine_registration(
        static, moving, static_affine, moving_affine)
    metric = metrics.CCMetric(3)  # Cross Correlation Metric for 3 dimensions
    level_iters = [100, 100, 30]  # Iterations at each resolution (fine
    #  to coarse)

    sdr = imwarp.SymmetricDiffeomorphicRegistration(metric, level_iters)
    sdr.verbosity = 0
    mapping = sdr.optimize(
        static, moving, static_affine, moving_affine, pre_align)
    warped_moving = mapping.transform(moving)

    return warped_moving, mapping
