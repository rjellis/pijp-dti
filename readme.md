# pijp-dti

All the steps necessary to for Diffusion Tensor Imaging.

## Stage

**Load the Dicoms and set up the pipeline**

Copies Dicom files for a particular DWI image code from a database and
converts them to a singular Nifti file with accompanying .bval and
.bvec files. Also creates the directories for all of the steps.

File Structure:

* project directory
    * subjects
        * image code
            * stage
            * prereg
            * reg
            * tenfit
            * roistats
        * another image code
            * stage
            * ...

## Preregister

**Denoise and skull strip the image**

Loads the staged Nifti file, denoises the image using Non Local Means,
and skull strips the image using a median Otsu thresholding method.
The denoised and masked image is saved as a compressed Nifti
(.nii.gz).

## Register

**Rigidly register the diffusion weighted directions to an averaged
b0 direction**

Loads the preregistered Nifti file, creates an average b0 image from the
b0 directions in the DWI, and rigidly registers all the diffusion
directions to the average b0 image. The b-vectors are updated to reflect
the orientation changes due to registration. The registered image is
saved as a compressed Nifti The updated b-vectors are saved as a
numpy file (.npy).

The average b0 image is created by rigidly registering all of the found
b0 directions to the first b0 direction and averaging the voxel
intensities.

## TensorFit

**Fit the diffusion tensor model**

Loads the registered Nifti file and calculates the eigenvalues and
eigenvectors (and more) by fitting the image to the diffusion tensor
model using Weighted Least Squares.

In addition to the eigenvalues and eigenvectors, various measures of
anisotropy are calculated:

* Fractional Anisotropy (FA)
* Mean Diffusivity (MD)
* Geodesic Anisotropy (GA)
* Axial Diffusivity (AD)
* Radial Diffusivity (RD)

Once the FA is generated, an atlas's FA is non-linearly registered using
symmetric diffeomorphic registration. While FA is chose for the
registration, the generated mapping applies to all the other anisotropy
measures as well. The mapping from this registration is also
applied to the atlas's labels [1]. The mapping is also inversely applied
to the subject FA, warping it into the atlas's space. The atlas FA and
label templates are stored in the module's 'templates' directory.

The anisotropy measures, warped FA, and warped labels are all saved as
compressed Nifti files. The eigenvalues and eigenvectors are also saved
as ndarrays in numpy files.

[1] 'labels' refer to an overlay that contains integer values that
correspond to regions in the brain

## RoiStats

**Generate CSV files for the statistics of various anisotropy measures in
certain regions of interest.**

*Work in progress*
