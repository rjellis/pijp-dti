# pijp-dti

All the steps necessary for Diffusion Tensor Imaging.


```
usage: dti.py [-h] [-s STEP] [-c CODE] [-p PROJECT] [-v] [-n NUMBER] [-d DELAY]

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

steps: stage, prereg, reg, tenfit, stats, store, maskqc, warpqc
```

## 1. Stage

**Convert Dicoms and set up the pipeline**

Copies Dicom files for a particular scan code from a database and
converts them to a singular Nifti file with accompanying .bval and
.bvec files using dcm2niix. Stage also creates the directories for all of the steps.

## 2. Preregister

**Denoise and skull strip the image**

Denoises each volume in the DWI shell using Non Local Means and generates a
skull stripped image using a median Otsu thresholding method.
The denoised image and the masked image are saved as compressed Nifti images (.nii.gz).

A mosaic (.png) of slices is created displaying the masked image overlaid
on the denoised image for the MaskQC step.

## 3. Register

**Rigidly register the diffusion weighted directions to an averaged
b0 direction**

Creates an average b0 volume and rigidly registers all the diffusion
directions to the average b0 volume. The b-vectors are updated to reflect
the orientation changes due to registration. The registered image is
saved as a compressed Nifti and updated b-vectors are saved as a
numpy file (.npy).

The average b0 image is created by rigidly registering all of the found
b0 directions to the first found b0 direction and averaging the voxel
intensities.

## 4. TensorFit

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
symmetric diffeomorphic registration. While FA is chosen for the
registration, the generated mapping applies to all the other anisotropy
measures as well. Forward mapping warps the template space to the subject space.
Inverse mapping warps the subject space to the template space.

The forward mapping from this registration is
applied to the atlas's labels [1] to warp them to the subject's space.
The inverse mapping is applied to the subject FA, warping it into the atlas's space.
The atlas FA and label templates are stored in the module's 'templates' directory.

The anisotropy measures, warped FA, warped labels, eigenvectors, and
eigenvalues are all saved as compressed Nifti files. The forward and
inverse mappings are saved as numpy files. The eigenvalue nifti image has three volumes
because every voxel has three eigenvalues. Likewise, the eigenvector nifti image has
nine volumes because every voxel has three eigenvectors of length 3.

[1] 'labels' refer to an overlay that contains integer values that
correspond to regions in the brain


## 5. RoiStats

**Generate CSV files for the statistics of various anisotropy measures in
certain regions of interest.**

The values for each anisotropy measure are found voxel-wise for each
region of interest. The minimum value, maximum value, mean, and standard
deviation are calculated for each region of interest. A comma separated
value file (CSV) is generated for each anisotropy measure. CSV
format: (name, min, max, mean, std. dev).

Voxels where the FA < 0.05 are set to zero. The ROI statistics are only
calculated over the non-zero voxels.
