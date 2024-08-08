#!/usr/bin/env python
from typing import List


import random
import time
import json
import sys
import subprocess
import os



import maxlab as mx

top_level_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.append(top_level_dir)

import bin.gui.GUI as GUI
from bin.lib.py_src.stimulation import Stimulation
import bin.lib.py_src.hal as hal


# STIM_ELECTRODES = {
#     0: [2907,4365,22677,23713],
#     2: [3315,6127,22413,22671]
# }
STIM_ELECTRODES = {
    0: [3319,3919,22243,22845],
    1: [3757,3929,22411,23115],
    2: [3765,3941,20483,21977],
    3: [4213,8323,23285,24017],
    4: [4653,5249,21971,23571],
    5: [6009,6965,19317,19655]
}
MINUTES = 60
THRESH = 0.1
STIM_RATE = 5 #stims per second?


if __name__ == '__main__':
    print(f"running {__file__}...")
    if len(sys.argv) > 1:
        f = open(sys.argv[1], "r")
        exp_args = json.load(f)
        f.close()
    else:
        f = open(GUI.start_gui(), "r")
        exp_args = json.load(f)
        f.close()

    trial_path = hal.make_trial_folders(exp_args)
        
    if exp_args['-MAXTWO-']:
        wells = exp_args['WELLS']
    else:
        wells = [0]

    file_name = exp_args["NAME"]


    mx.clear_events() 
    
    well_data = {}
    for well in wells:
        rec_electrodes = exp_args["CONFIGS"][str(well)]["E_NUMS"]
        does_stimulations = True

        array = hal.init_well(well, rec_electrodes, STIM_ELECTRODES[well])

        well_data[well] = hal.get_file_names(well, file_name, trial_path)

        array.save_config(well_data[well]["CFG"])
        
        ############################################################################

        mx.offset()

        single_pulse = Stimulation(f"pulse{well}", 0, 50, 200, 1, 1, 10, 1, well = well)
        duration = single_pulse.get_duration()
        single_pulse.build_sequence(initial_delay = 0)

        #Create start train and end sequences. TODO: LOOP THROUGH ALL WELLS AND DO THIS
        hal.build_training_sequences(well)
        
        program_args = [f"./bin/build/rp_stim_removal", "2>", "ERR_LOG", "--config", well_data[well]["CFG"], "--folder", well_data[well]["REC_DIR"], "--pulse_duration", str(duration)]
        if exp_args['-MAXTWO-']:
            program_args.append("--maxtwo")

        #TODO: put them on top to change from run to run
        program_args.append("--threshold")
        program_args.append(str(THRESH))
        program_args.append("--minutes")
        program_args.append(str(MINUTES))
        program_args.append("--well")
        program_args.append(str(well))
        program_args.append("--stim_rate")
        program_args.append(str(STIM_RATE))

        well_data[well]["ARGS"] = program_args

        #############################################################################

    for well in wells:
        mx.activate([well])
        mx.set_primary_well(well)
        
        s = mx.Saving()
        s.open_directory(well_data[well]["REC_DIR"])
        s.start_file(well_data[well]["REC_FILE"])

        #Write metadata
        hal.write_exp_description(s, f"Removal of noxious stimuli to train burst direction. Stim frequency: {STIM_RATE} Hz. Threshold: {THRESH}. Time: {MINUTES} mins.")
        hal.write_stim_electrodes(s, STIM_ELECTRODES[well])
        hal.write_closed_loop_args(s, well_data[well]["ARGS"])

        s.group_delete_all()
        
        s.group_define(well, f"all_channels_{well}", list(range(1024)))

        print("recording... well " + str(well))
        s.start_recording([well])
        
        ############################################################################
        
        print("calling c++ script... well" + str(well))

        mx.send(mx.Event(well, 1, 1, "start_subprocess 1"))
        try:
            subprocess.run(well_data[well]["ARGS"])
        except KeyboardInterrupt:
            print("start-maxlab.py: ^C signalled")
        except Exception as err:
            print(err)

        mx.send(mx.Event(well, 1, 1, "end_subprocess 1"))


        print("c++ script over...")

        ############################################################################

        s.stop_recording()
        s.stop_file()
        s.group_delete_all()
        print("finished recording")
