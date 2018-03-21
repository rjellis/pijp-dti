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

steps: stage, denoise, register, mask, apply, tenfit, warp, seg, stats, maskqc, segqc, warpqc, store
```

# Table of Contents
1. [Stage](#Stage)
2. [Denoise](#Denoise)
3. [Register](#Register)
4. [Mask](#Mask)
5. [MaskQC](#MaskQC)
6. [ApplyMask](#ApplyMask)
7. [TensorFit](#TensorFit)
8. [Warp](#Warp)
9. [Segment](#Segment)
10. [RoiStats](#RoiStats)
11. [SegQC](#SegQC)
12. [WarpQC](#WarpQC)
13. [StoreInDatabase](#Store)
14. [How To](#HowTo)

## 1. Stage <a name="Stage"></a>

**Convert Dicoms and set up the pipeline**

Copies Dicom files for a particular DWI scan code from a database and
converts them to a singular Nifti file with accompanying .bval and
.bvec files using dcm2niix. Stage also creates the directories for all of the steps.
Staging will not overwrite a case directory if it already exists, use `--force` if you wish
to do so.

```
Step Flag Name: step
Directory Name: 0Stage

Output Files:
    DWI: SampleCode.nii.gz
    b values: SampleCode.bval
    b vectors: SampleCode.bvec
```

## 2. Denoise <a name="Denoise"></a>

**Denoise the DWI using Local PCA**

Denoises the entire 4D shell using Local PCA.

```
Step Flag Name: denoise
Directory Name: 1Denoise

Output Files:
    denoised DWI: SampleCode_denoised.nii.gz
```


## 3. Register <a name="Register"></a>

**Rigidly register the diffusion weighted directions to an averaged
b0 direction**

Creates an average b0 volume and rigidly registers all the diffusion
directions to the average b0 volume to correct for subject motion.
The b-vectors are updated to reflect the orientation changes due to registration.
The average volume and the registered image are saved as a compressed
Niftis and the transformation matrices and updated b-vectors are saved as CSV's. The average b0 volume
is created by rigidly registering all of the found b0 directions to the first found b0 direction and averaging the voxel
intensities.

```
Step Flag Name: register
Directory Name: 2Register

Output files:
    b0 volume: SampleCode_b0.nii.gz
    registered DWI: SampleCode_reg.nii.gz
    registraiton map (Python pickle): SampleCode_reg_map.p
    b values: SampleCode_bval.csv
    b vectors (original): SampleCode_bvec.csv
    b vectors (registered): SampleCode_bvec_reg.csv
```

## 4. Mask <a name="Mask"></a>

**Skull Strip the b0 volume**

Checks if the mask has been completed by the NNICV pipeline. If the mask exists, the subject's
T2 is registered (affine) to the b0 volume. The transform is then applied to the NNICV mask and
saved as the auto mask.
If the NNICV mask is not found, the average b0 volume is masked using Median Otsu Threshodling.
Holes in the binary mask are filled with scipy's binary_fill_holes. The largest element of
the mask is extracted to remove extraneous pieces of the mask.

```
Step Flag Name: mask
Directory Name: 3Mask

Output Files:
    auto mask: SampleCode_auto_mask.nii.gz

    Only generated if the NNICV mask exists:
    NNICV mask: SampleCode_nnicv.nii.gz
    T2: SampleCode_t2.nii.gz
    T2 (registered to b0 volume): SampleCode_t2_reg.nii.gz
```

## 5. MaskQC <a name="MaskQC"></a>

**Open a GUI to QC the automated skull stripping**

Selecting **Pass, Fail, or Edit** sets the result for the case being QC'd. A result of
**Pass** or **Edit** will run ApplyMask.

```
Step Flag Name: maskqc

Has a queue mode!
```


## 6. ApplyMask <a name="ApplyMask"></a>

**Applies the generated or edited b0 mask to the DWI**

Saves a copy of the automatic mask (as the final mask)
and applies the final mask to the registered DWI.

```
Step Flag Name: apply
Directory Name: 3Mask

Output Files:
    final mask: SampleCode_final_mask.nii.gz
    masked DWI: SampleCode_masked.nii.gz
```

## 7. TensorFit <a name="TensorFit"></a>

**Fit the diffusion tensor model**

Calculates the eigenvalues and eigenvectors (and more) by fitting the
DWI to the diffusion tensor model using Weighted Least Squares.
In addition to the eigenvalues and eigenvectors, various measures of
anisotropy are also calculated:

* Fractional Anisotropy (FA)
* Mean Diffusivity (MD)
* Geodesic Anisotropy (GA)
* Axial Diffusivity (AD)
* Radial Diffusivity (RD)

Each measure of anisotropy is a 3D volume in the same space as the subject.
The anisotropy measures, eigenvectors, and eigenvalues are all saved as compressed Nifti files.

```
Step Flag Name: tenfit
Directory Name: 4Tenfit

Output Files:
    eigen values: SampleCode_evals.nii.gz
    eigen vectors: SampleCode_evecs.nii.gz
    FA: SampleCode_fa.nii.gz
    MD: SampleCode_md.nii.gz
    GA: SampleCode_ga.nii.gz
    RD: SampleCode_rd.nii.gz
```

## 8. Warp <a name="Warp"></a>

An Atlas's FA is non-linearly registered to the subject FA using
symmetric diffeomorphic registration. Forward mapping warps the template
space to the subject space. Inverse mapping warps the subject space
to the template space.

```
Step Flag Name: warp
Directory Name: 5Warp

Output Files:
    Warp map (Atlas to Subject): SampleCode_warp_map.p
    Warped labels: SampleCode_warped_labels.nii.gz
    FA (Atlas space): SampleCode_inverse_warped_fa.nii.gz
```


## 9. Segment <a name="Segment"></a>

The registered b0 image is segmented into 4 tissue classes: background, white matter,
gray matter, and CSF. The white matter segmentation is then
applied as a mask to the warped labels.

```
Step Flag Name: segment
Directory Name: 6Segment

Output Files:
    Segmented b0 (4 volumes): SampleCode_segmented.nii.gz
    b0 white matter: SampleCode_segmented_wm.nii.gz
    Warped white matter labels: SampleCode_warped_wm_labels.nii.gz
```


## 10. RoiStats <a name="RoiStats"></a>

**Generate CSV files for the statistics of various anisotropy measures in
certain regions of interest**

The values for each anisotropy measure are found voxel-wise for each
region of interest. The minimum value, maximum value, mean, standard
deviation, median and volume are calculated for each region of interest.
A comma separated value file (CSV) is generated for each anisotropy measure.
CSV format: (name, min, max, mean, std. dev, median, volume).
The white matter segmentation mask is applied before calculation.
The ROI statistics are only calculated over the non-zero voxels.

```
Step Flag Name: stats
Directory Name: 7Stats

Output Files:
    FA stats: SampleCode_fa_roi.csv
    MD stats: SampleCode_md_roi.csv
    GA stats: SampleCode_ga_roi.csv
    AD stats: SampleCode_ad_roi.csv
    RD stats: SampleCode_rd_roi.csv
```

## 11. SegQC <a name="SegQC"></a>

**Open a GUI to QC the tissue segmentation**

Runs WarpQC if **Pass** is submitted. Queues up cases where RoiStats is done.

```
Step Flag Name: segqc

Has a queue mode!
```

## 12. WarpQC <a name="WarpQC"></a>

**Open a GUI to QC the nonlinear registration**

If **Pass** is submitted, the results from RoiStats are stored in the Database.

```
Step Flag Name: warpqc
```

## 13. StoreInDatabase <a name="Store"></a>

Store the CSV's from RoiStats in the database (Imaging.pijp_dti) after passing WarpQC.

# How To <a name="HowTo"></a>

1) Use step `stage` to run the pipeline for some code(s)

```
For single case:
    dti.py -p SampleProject -c SampleCode -s stage

Queue Mode:
    dti.py -p SampleProject -s stage -n 10
```

This will run the code(s) through steps 1-4 unless `--nocontinue` was used.
The code(s) will be ready for MaskQC once step 4 (Mask) is complete. The flag `-n 10` tells
the pipeline to stage 10 cases. Omitting the `-n` flag will tell the pipeline to run over all available cases that
have not already been staged.
If you wish to restage a case, use the flag `--force`. **Warning! This will delete the entire case folder, including the
edited masks!**


2) Use `maskqc` to QC the completed code(s)

```
   dti.py -p SampleProject -s maskqc
````

Only submit the result of **Edit** after you have completely finished editing the mask.
If you are not done editing but want to exit, just save the mask in FSLeyes and exit
the QC Tool without submitting. Rerunning this step in queue mode will reopen the last unfinished case.

**When saving the edited mask, be sure you are overwriting "SampleCode_final_mask.nii.gz" in
  SampleCode's "3Mask" directory!**


3) Use `segqc` to start the final QC

```
   dti.py -p SampleProject -s segqc
```

`segqc` will automatically run for the case if `maskqc` is passed, unless `--nocontinue`
was used. Likewise, `warpqc` will automatically run if `segqc` is passed. Once `warpqc` is completed,
the pipeline is done!

### Notes

- Generally, step 2 (Denoise) and step 3 (Register) take the longest to complete
- Exiting the QC Tool will cancel the queue and stop the pipeline
- In queue mode, `maskqc` will first reopen the last code that was cancelled (but not skipped)

