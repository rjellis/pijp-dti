# pijp-dti

All the steps necessary to process diffusion weighted images.

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

steps: stage*, denoise, register, mask, apply*, tenfit, warp, seg, stats, maskqc*, segqc*, warpqc*, store

* steps with queue modes

```

## 1. Stage

**Convert Dicoms and set up the pipeline**

Copies Dicom files for a particular DWI scan code from a database and
converts them to a singular Nifti file with accompanying .bval and
.bvec files using dcm2niix. Stage also creates the directories for all of the steps.

Staging will not overwrite a case directory if it already exists, use '--force' if you wish
to do so.

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
Niftis and the transformation matrices and updated b-vectors are saved as a numpy files (.npy).

The average b0 volume is created by rigidly registering all of the found
b0 directions to the first found b0 direction and averaging the voxel
intensities.

## 4. Mask

**Skull Strip the b0 volume**

Masks the average b0 volume using median Otsu thresholding. Holes in the binary mask
are filled with scipy's binary_fill_holes. The largest element of the mask is extracted
to remove extraneous pieces of the mask.

## 5. ApplyMask

**Applies the generated or edited b0 mask to the DWI**

Saves a copy of the automatic mask (as the final mask)
and applies the binary mask to the copy.

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

## 8. Segment

The registered b0 image is segmented into 4 tissue classes: background, white matter,
gray matter, and CSF. The white matter segmentation is applied as a mask to the warped labels
for clarity during QC.

## 9. RoiStats

**Generate CSV files for the statistics of various anisotropy measures in
certain regions of interest**

The values for each anisotropy measure are found voxel-wise for each
region of interest. The minimum value, maximum value, mean, standard
deviation, median and volume are calculated for each region of interest.
A comma separated value file (CSV) is generated for each anisotropy measure.
CSV format: (name, min, max, mean, std. dev, median, volume).
The white matter segmentation mask is applied before calculation. It thresholds
where the probability for white matter is greater than or equal to 40%.
The ROI statistics are only calculated over the non-zero voxels.

## Interactive Steps

### MaskQC

**Open a GUI to QC the automated skull stripping**

Selecting **'Pass', 'Fail', or 'Edit'** sets the result for the case being QC'd.
Runs SegQC if 'pass' is selected.

### SegQC

**Open a GUI to QC the tissue segmentation**

Runs WarpQC if 'pass' is selected. Queues up cases where MaskQC is passed or edited
cases where RoiStats has an outcome of 'Redone.'

### WarpQC

**Open a GUI to QC the nonlinear registration**

Queues up cases where SegQC has passed.
If 'pass' is selected, the results from RoiStats are stored in the Database.

### StoreInDatabase

Store the CSV's from RoiStats in the database after passing WarpQC.

# How To Use

1) Use step `stage` to run the pipeline for some code(s)

       ```
       examples:
       dti.py -p SampleProject -c SampleCode -s stage
       ```
2) Use step `maskqc` to QC the completed code(s)

sample command for QC:

`dti.py -p SampleProject -s maskqc`

This will queue up all cases ready for MaskQC. A window will open with the
middle slice of the average b0 image, with a red mask overlaid. Use the **Pass, Edit, or Fail**
buttons on the right to select a result. Select **Open in FSLView** if you wish to edit the
mask or view the case with a more advanced viewer. When you are done editing or selecting a result,
use the **Submit** button to submit the case. This button will close the current window. If you wish to
exit the QC Tool at any time, use the **Quit** button. This will close the QC Tool and stop the queue.
Running the MaskQC command again will continue where you left off.
If you wish to open a single case, use the option `-c` followed by the desired code in the command.


