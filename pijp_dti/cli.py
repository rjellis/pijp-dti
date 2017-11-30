import os
import sys
import subprocess

import click

from pijp_dti import dti


@click.command()
@click.option('--step', '-s', multiple=True, help="Specify the step(s) to do")
@click.option('--verbose', '-v', is_flag=True, help="Show runtime messages")
@click.option('--convert', '-c', is_flag=True, help="Convert files in input directory from dicom to nifti")
@click.argument('input_dir', type=click.Path(exists=True))
@click.argument('output_dir', type=click.Path())
def cli(step, verbose, convert, input_dir, output_dir):
    """
    Diffusion Tensor Pipeline

        The input directory must have a 4D diffusion weighted image Nifti file (.nii or .nii.gz) with accompanying
        b-value and b-vector files (.bval/.bvec). The input directory may also be a parent directory containing
        subdirectories with these required files.

        Possible steps: stage, prereg, reg, tenfit, roi

    """
    # load defaults from config file (verbosity, steps , dcm2nii path, etc)
    # make option to display the default config

    if verbose:
        enable_print()

    if not verbose:
        block_print()

    it = os.scandir(input_dir)
    for entry in it:
        if os.path.isdir(entry.path):
            code = entry.name
            pipe(output_dir, code, entry.path, step)
        elif os.path.isfile(entry.path):
            path = entry.name.split('.')
            if path[-1] == 'nii' or path[-1] == 'gz':
                pipe(output_dir, path[0], input_dir, step)


def pipe(out_path, code, in_path, step):
    stage = dti.Stage(out_path, code, in_path)
    prereg = dti.Preregister(out_path, code, in_path)
    reg = dti.Register(out_path, code, in_path)
    tenfit = dti.TensorFit(out_path, code, in_path)
    roi_stats = dti.RoiStats(out_path, code, in_path)
    qc = dti.MaskQC(out_path, code, in_path)
    steps = {'stage': stage, 'prereg': prereg, 'reg': reg, 'tenfit': tenfit, 'roi': roi_stats, 'qc': qc}

    if not step:
        stage.run()
        prereg.run()
        reg.run()
        tenfit.run()
        roi_stats.run()
        qc.run()

    else:
        for stp in step:
            if stp in steps:
                steps[stp].run()


def block_print():
    sys.stdout = open(os.devnull, 'w')


def enable_print():
    sys.stdout = sys.__stdout__


def run_cmd(cmd):
    args = cmd.split()
    p = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)