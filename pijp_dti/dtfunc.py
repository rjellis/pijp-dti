import numpy as np

from dipy.core import gradients
from dipy.segment import mask as otsu
from dipy.reconst import dti
from dipy.align import (imaffine, imwarp,
                        transforms, metrics)
from dipy.denoise import noise_estimate, nlmeans
from dipy.denoise.localpca import localpca
from dipy.denoise.pca_noise_estimate import pca_noise_estimate


def mask(dat):
    """Skull strip using the Median Otsu method.

    median_radius is the radius (in voxels) for the median filter
    num_pass is the number of passes of the median filter

    Args:
        dat (ndarray): 3D numpy ndarray.

    Returns:
        mask_dat (ndarray): The masked ndarray.

    """
    mask_dat, bin_dat = otsu.median_otsu(dat, median_radius=2, numpass=4)
    return mask_dat


def denoise(dat):
    """Denoise a data set using Non Local Means.

    Args:
        dat (ndarray): 3D or 4D numpy ndarray

    Returns:
        denoise_dat (ndarray): The denoised ndarray

    """
    sigma = noise_estimate.estimate_sigma(dat)
    denoise_dat = nlmeans.nlmeans(dat, sigma)
    return denoise_dat


def denoise_pca(dat, bval, bvec):
    """Denoise a data set using Local PCA.

    Local PCA is a denoising method specific to 4D diffusion weighted images.

    Args:
        dat (ndarray): 3D or 4D numpy ndarray
        bval (ndarray): 1D ndarray containing the b-values for the DWI directions
        bvec (ndarray): 2D ndarray containing the b-vectors for the DWI directions

    Returns:
        denoise_dat (ndarray): The denoised ndarray

    """
    gtab = gradients.gradient_table(bval, bvec)
    sigma = pca_noise_estimate(dat, gtab, correct_bias=True, smooth=3)
    denoise_dat = localpca(dat, sigma=sigma, patch_radius=2)
    return denoise_dat


def b0_avg(dat, aff, bval):
    """Obtain the average b0 image from a 4D DWI image.

    All b0 directions are registered to the first found b0 so they all share an affine.

    Args:
        dat (ndarray): 4D ndarray of a diffusion weighted image.
        aff (ndarray): 4 X 4 ndarray of the affine of the image.
        bval (ndarray): 1D ndarray containing the b-values for the DWI directions

    Returns:
        b0 (ndarray): 3D ndarray of the averaged b0 image.

    """
    x, y, z, d = dat.shape
    b0_dir = 0
    b0_count = np.count_nonzero(bval == 0)
    b0_dat = np.ndarray(shape=(x, y, z, b0_count))

    for i in range(0, bval.shape[0]):
        if bval[i] == 0:
            b0_dat[:, :, :, b0_dir] = dat[:, :, :, i]
            b0_dir += 1
    b0_sum = np.zeros(shape=b0_dat[..., 0].shape)
    b0_aff = aff

    for i in range(0, b0_dir):
        b0_dat_reg, b0_aff = affine_registration(b0_dat[..., 0], b0_dat[..., i], aff, b0_aff, rigid=True)
        b0_sum = np.add(b0_sum, b0_dat_reg)

    b0 = b0_sum / b0_dir

    return b0


def register(b0, dat, b0_aff, aff, bval, bvec):
    """Rigidly register a 4D DWI to its own 3D b0 image.

    Args:
        b0 (ndarray): 3D ndarray of the stacked b0 image.
        dat (ndarray): 4D array of the DWI image containing b0 and diffusion weighted directions
        b0_aff (ndarray): 4 X 4 affine matrix for the b0
        aff (ndarray): 4 X 4 affine matrix for the DWI
        bval (ndarray): 1D ndarray containing the b-values for the DWI directions
        bvec (ndarray): 1D ndarray containing the b-vectors for the DWI directions

    Returns:
        reg_dat (ndarray): 4D ndarray of the registered DWI
        reg_bvecs (ndarray): 2D ndarray of the updated b-vectors

    """
    affines = []
    reg_dat = np.zeros(shape=dat.shape)
    for i in range(0, dat.shape[3]):
        reg_dir, reg_aff = affine_registration(b0, dat[..., i], b0_aff, aff, rigid=True)
        reg_dat[..., i] = reg_dir
        if bval[i] != 0:
            affines.append(reg_aff)

    gtab = gradients.gradient_table(bval, bvec)
    new_gtab = gradients.reorient_bvecs(gtab, affines)
    reg_bvecs = new_gtab.bvecs

    return reg_dat, reg_bvecs


def fit_dti(dat, bval, bvec):
    """Fit the tensor using the Weighted Least Squares fit method.

    Args:
        dat (ndarray): 4D ndarray of the diffusion weighted image.
        bval (ndarray): 1D ndarray containing the b-values for the DWI directions.
        bvec (ndarray): 2D ndarray containing the b-vectors for the DWI directions.

    Returns:
        evals (ndarray): 4D ndarray of the eigenvalues for every voxel
        evecs (ndarray): 5D ndarray of the eigenvectors for every voxel
        tenfit (TensorFit object): TensorFit object containing the evals, evecs and other DTI measures

    """
    gtab = gradients.gradient_table(bval, bvec)
    tenmodel = dti.TensorModel(gtab)
    dat, bin_mask = otsu.median_otsu(dat)
    tenfit = tenmodel.fit(dat, bin_mask)
    evals = tenfit.evals
    evecs = tenfit.evecs

    return evals, evecs, tenfit


def roi_stats(dat, overlay, labels):
    """Get statistics on a diffusion tensor measure in specific regions of interest.

    Args:
        dat (ndarray): 3D ndarray of an diffusion tensor measurement such as: Fractional Anisotropy,
                       Mean Diffusivity, etc.
        overlay (ndarray): 3D ndarray with the same dimension of dat.
        labels (Union): A dictionary of overlay values as keys that correspond to region labels as dictionary values.

    Returns:
        avgs (dict): A dictionary of the region labels as keys and the averages for those regions as values.

    """
    # TODO do this better (don't return a dict)
    # TODO also add min, max, std dev

    avgs = dict()
    vals = labels.values()
    for names in vals:
        avgs[names] = [0, 0]

    for coord, val in np.ndenumerate(dat):
        key = overlay[coord]
        if key in labels:
            avgs[labels[key]] = [avgs[labels[key]][0] + val, avgs[labels[key]][1] + 1]

    avg_keys = avgs.keys()
    for akey in avg_keys:
        if avgs[akey][1] == 0:
            avgs[akey] = 0
        else:
            avgs[akey] = avgs[akey][0] / avgs[akey][1]

    return avgs


def affine_registration(static, moving, static_affine, moving_affine, rigid=False):
    """Register one 3D array to another using linear registration.

    Args:
        static (ndarray): 3D ndarray that is being used as reference.
        moving (ndarray): 3D ndarray that is being registered.
        static_affine (ndarray): 4 X 4 affine matrix of the static image.
        moving_affine (ndarray): 4 X 4 affine matrix of the moving image.
        rigid (bool): A selector for rigid registration instead of affine registration.

    Returns:

        dat_reg (ndarray): The registered moving 3D ndarray.
        rigid.affine (ndarray): 4 X 4 affine matrix of the registered image if rigid is selected.
        affine.affine (ndarray): 4 X 4 affine matrix of the registered image if affine is selected.

    """
    # Mutual information Metric
    nbins = 32  # Number of bins for computing the histograms
    sampling_prop = None  # percentage of voxels for computing MI (0, 100]
    metric = imaffine.MutualInformationMetric(nbins, sampling_prop)
    level_iters = [100, 50, 30]  # Iterations at each resolution (coarse to fine)
    sigmas = [3.0, 1.0, 0.0]
    factors = [4, 2, 1]  # Factors that determine resolution

    affreg = imaffine.AffineRegistration(metric,
                                         level_iters=level_iters,
                                         sigmas=sigmas,
                                         factors=factors,
                                         verbosity=0)
    params0 = None

    c_of_mass = imaffine.transform_centers_of_mass(
        static, static_affine,
        moving, moving_affine)

    if rigid:
        rig_map = affreg.optimize(
            static, moving,
            transforms.RigidTransform3D(),
            params0, static_affine,
            moving_affine, c_of_mass.affine)
        dat_reg = rig_map.transform(moving)
        return dat_reg, rig_map.affine

    if not rigid:
        aff_map = affreg.optimize(
            static, moving,
            transforms.AffineTransform3D(),
            params0, static_affine,
            moving_affine, c_of_mass.affine)
        dat_reg = aff_map.transform(moving)
        return dat_reg, aff_map.affine


def symm_diff_registration(static, moving, static_affine, moving_affine):
    """Register one 3D array to another using non-linear registration.

    Args:
        static (ndarray): 3D ndarray that is being used as reference.
        moving (ndarray): 3D ndarray that is being registered.
        static_affine (ndarray): 4 X 4 affine matrix of the static image.
        moving_affine (ndarray): 4 X 4 affine matrix of the moving image.

    Returns:
        warped_moving (ndarray): The registered moving 3D ndarray
        mapping (DiffeomorphicMap): The mapping object to warp 3D ndarrays to the obtained registration

    """
    moving_reg, pre_align = affine_registration(static, moving, static_affine, moving_affine)
    metric = metrics.CCMetric(3)  # Cross Correlation Metric for 3 dimensions
    level_iters = [30, 50, 100]  # Iterations at each resolution (fine to coarse)

    sdr = imwarp.SymmetricDiffeomorphicRegistration(metric, level_iters)
    mapping = sdr.optimize(static, moving, static_affine, moving_affine, pre_align)
    warped_moving = mapping.transform(moving)

    return warped_moving, mapping
