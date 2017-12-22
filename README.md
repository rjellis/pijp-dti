# pijp-dti

All the steps necessary to process Diffusion Tensor Images.


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

steps: stage, denoise, register, mask, tenfit, warp, stats, store, maskqc, warpqc
```

## 1. Stage

**Convert Dicoms and set up the pipeline**

Copies Dicom files for a particular DWI scan code from a database and
converts them to a singular Nifti file with accompanying .bval and
.bvec files using dcm2niix. Stage also creates the directories for all of the steps.

## 2. Denoise

**Denoise the DWI using Local PCA**

Denoises the entire 4D shell using Local PCA.


## 3. Register

**Rigidly register the diffusion weighted directions to an averaged
b0 direction**

Creates an average b0 volume and rigidly registers all the diffusion
directions to the average b0 volume to correct for subject motion.
The b-vectors are updated to reflect the orientation changes due to registration.
The average volume and the registered image are saved as a compressed
Niftis and updated b-vectors are saved as a numpy file (.npy).

The average b0 volume is created by rigidly registering all of the found
b0 directions to the first found b0 direction and averaging the voxel
intensities.

## 4. Mask

**Skull Strip the b0 volume**

Masks the average b0 volume using median Otsu thresholding.

## 5. ApplyMask

**Applies the generated or edited b0 mask to the DWI**

First tries to apply the edited mask if it exists. If there is no
edited mask saved, then the auto mask is applied to the denoised DWI
and saved in the 'mask' directory.

## 6. TensorFit

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

The anisotropy measures, warped FA, warped labels_lookup, eigenvectors, and
eigenvalues are all saved as compressed Nifti files. The forward and
inverse mappings are saved as numpy files. The eigenvalue nifti image has three volumes
because every voxel has three eigenvalues. Likewise, the eigenvector nifti image has
nine volumes because every voxel has three eigenvectors of length 3.



## 7. Warp

An Atlas's FA is non-linearly registered to the subject FA using
symmetric diffeomorphic registration. While FA is chosen for the
registration, the generated mapping applies to all the other anisotropy
measures as well. Forward mapping warps the template space to the subject space.
Inverse mapping warps the subject space to the template space.


## 8. RoiStats

**Generate CSV files for the statistics of various anisotropy measures in
certain regions of interest**

The values for each anisotropy measure are found voxel-wise for each
region of interest. The minimum value, maximum value, mean, and standard
deviation are calculated for each region of interest. A comma separated
value file (CSV) is generated for each anisotropy measure. CSV
format: (name, min, max, mean, std. dev).

Voxels where FA < 0.05 are set to zero. The ROI statistics are only
calculated over the non-zero voxels.

## Interactive Steps

### MaskQC

**Launch a GUI to QC the automated skull stripping**

Runs WarpQC if 'pass' is selected. If 'Save Edited Mask' is selected,
a file dialog opens to get the path of the edited mask.

### WarpQC

**Launch a GUI to QC the nonlinear registration**

If 'pass' is selected, the results from RoiStats are stored in the Database.

### StoreInDatabase

Store the CSV's from RoiStats in the database after passing WarpQC.
