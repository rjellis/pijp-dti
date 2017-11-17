import os
import sys
import time

from pijp_dti import dti


def run(project, code, args):
    stage = dti.Stage(project, code, args)
    prereg = dti.Preregister(project, code, args)
    reg = dti.Register(project, code, args)
    tenfit = dti.TensorFit(project, code, args)
    roiavg = dti.RoiStats(project, code, args)

    start_time = time.time()
    print("Running pipeline for {}".format(code))
    print("    Staging...")
    stage_time = time.time()
    stage.run()
    print("        Staging took {:.2f} seconds".format(time.time()-stage_time))

    print("    Preregistering...")
    prereg_time = time.time()
    prereg.run()
    print("        Preregistering took {:.2f} seconds".format(
                        time.time()-prereg_time))

    print("    Registering...")
    reg_time = time.time()
    reg.run()
    print("        Registering took {:.2f} seconds".format(
                        time.time()-reg_time))

    print("    Fitting tensor...")
    sys.stdout = open(os.devnull, 'w')
    tenfit_time = time.time()
    tenfit.run()
    sys.stdout = sys.__stdout__
    print("        Fitting took {:.2f} seconds".format(
                        time.time()-tenfit_time))

    print("    Averaging tensor measure per ROI...")
    roi_time = time.time()
    roiavg.run()
    print("        ROI averaging took {:.2f} seconds".format(
                        time.time()-roi_time))

    print("Pipeline complete!")
    run_time = time.time()-start_time
    print("    Pipeline took {} minute(s) and {:.2f} second(s)".format(run_time//60,
          run_time-(60*(run_time//60))))
