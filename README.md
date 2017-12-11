# pijp-dti

All the steps necessary for Diffusion Tensor Imaging.


```
usage: pijp-dti [-h] [-s STEP] [-c CODE] [-p PROJECT] [-v] [-n NUMBER] [-d DELAY]

optional arguments:
  -h, --help            show this help message and exit
  -s STEP, --step STEP  The step to execute.
  -c CODE, --code CODE  The code of a particular case.
  -p PROJECT, --project PROJECT
                        The name of a project to work with
  -v, --verbose         Tell me all about it.
  -n NUMBER, --number NUMBER
                        The number of jobs to run when using queue mode.
  -d DELAY, --delay DELAY
                        Number of seconds to delay between jobs

steps: stage, prereg, reg, tenfit, stats
```

## Stage

**Convert Dicoms and set up the pipeline**

Copies Dicom files for a particular scan code from a database and
converts them to a singular Nifti file with accompanying .bval and
.bvec files using dcm2niix. Also creates the directories for all of the steps.

## Preregister

**Denoise and skull strip the image**

Denoises the image using Non Local Means and skull strips the image using a median Otsu thresholding method.
The denoised is saved as a compressed Nifti (.nii.gz) and the binary mask is saved as ndarray in a numpy file (.npy).

## Register

**Rigidly register the diffusion weighted directions to an averaged
b0 direction**

Creates an average b0 image from the
b0 directions in the DWI and rigidly registers all the diffusion
directions to the average b0 image. The b-vectors are updated to reflect
the orientation changes due to registration. The registered image is
saved as a compressed Nifti The updated b-vectors are saved as a
numpy file (.npy).

The average b0 image is created by rigidly registering all of the found
b0 directions to the first found b0 direction and averaging the voxel
intensities.

## TensorFit

**Fit the diffusion tensor model**

Calculates the eigenvalues and eigenvectors (and more) by fitting the
image to the diffusion tensor model using Weighted Least Squares.

In addition to the eigenvalues and eigenvectors, various measures of
anisotropy are also calculated:

* Fractional Anisotropy (FA)
* Mean Diffusivity (MD)
* Geodesic Anisotropy (GA)
* Axial Diffusivity (AD)
* Radial Diffusivity (RD)

Each measure of anisotropy is a 3D volume in the same space as the subject.
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

The values for each anisotropy measure are found voxel-wise for each
region of interest. The minimum value, maximum value, mean, and standard
deviation are calculated for each region of interest. A comma separated
value file (CSV) is generated for each anisotropy measure. CSV
format: (name, min, max, mean, std. dev).
