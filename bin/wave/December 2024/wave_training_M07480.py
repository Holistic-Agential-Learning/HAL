#!/usr/bin/env python
from typing import List

from datetime import datetime
import time
import sys
import subprocess
import os
import time

import maxlab as mx

top_level_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.append(top_level_dir)

from bin.lib.py_src.stimulation import Stimulation
import bin.lib.py_src.hal as hal


#TODO configs
# the index of each element in the list corresponds to a well number
#
all_configs = [
    "",
    "",
    "",
    "",
    "",
    ""
]

# stimulation type for right vs left bursts: 0 for none, 1 for regular, 2 for 
# random
right = 0
left = 2

#TODO indicates whether to simply read data, or to stimulate the buttons manually
live_chip = True

#TODO
wells = [0, 1, 2, 3, 4, 5]

# TODO
#
# full path to parent directory of experiment data
#
# data for each trial will be saved in "parent_dir/experiment_name/chip_id/date/trial"
parent_dir = "/home/mxwbio/Desktop/HAL/data/wave-training"

#TODO 
experiment_name = "dec-2024"

#TODO
chip_id = "M07480" 

#TODO
maxtwo = True

#TODO 
# in minutes, float
pre_exp_time = 20
experiment_time = 20
post_exp_time = 20

#TODO
#
#
threshold = 0.1

#TODO stims per second
stim_rate = 5

#TODO stimulation electrodes
stim_electrodes = [
    [],
    [],
    [],
    [],
    [],
    []
]


#TODO desription
desc = f"No stimulation for rightwards bursts and regular stimulation for leftwards. Stim frequency: {stim_rate} Hz. Threshold: {threshold}. Time: {experiment_time} mins."

#TODO
#
# emails to notify after the experiment ends
emails = ["sydney.palmer@tufts.edu"]

def get_time():
    return datetime.now().time().strftime("%H:%M")


if __name__ == '__main__':

    trial_path = hal.make_trial_folders_raw(parent_dir, experiment_name, chip_id, wells)

    mx.clear_events() 
    
    for well in wells:
        rec_electrodes = all_configs[well]

        print(stim_electrodes[well])

        array = hal.init_well(well, rec_electrodes, stim_electrodes[well])

        dir, h5, config_name = hal.get_file_names(well, experiment_name, trial_path)

        array.save_config(config_name)
        
        ############################################################################

        single_pulse = Stimulation(f"pulse{well}", 0, 250, 200, 1, 1, 10, 1, well = well)
        duration = single_pulse.get_duration()
        single_pulse.build_sequence(initial_delay = 0)
        
        hal.build_training_sequences(well)
        
        program_args = [f"./bin/build/train-wave", "--config", config_name, "--folder", dir, "--pulse-duration", str(duration)]
        
        if maxtwo:
            program_args.append("--maxtwo")

        #TODO: put them on top to change from run to run
        program_args.append("--threshold")
        program_args.append(str(threshold))
        program_args.append("--pre-recording")
        program_args.append(str(pre_exp_time))
        program_args.append("--post-recording")
        program_args.append(str(post_exp_time))
        program_args.append("--minutes")
        program_args.append(str(experiment_time))
        program_args.append("--well")
        program_args.append(str(well))
        program_args.append("--stim-rate")
        program_args.append(str(stim_rate))
        program_args.append("--right-type")
        program_args.append(str(right))
        program_args.append("--left-type")
        program_args.append(str(left))

        #############################################################################

        mx.activate([well])
        mx.set_primary_well(well)
        
        s = mx.Saving()
        s.open_directory(dir)
        s.start_file(h5)

        #Write metadata
        hal.write_exp_description(s, desc)
        hal.write_stim_electrodes(s, stim_electrodes[well])
        hal.write_closed_loop_args(s, program_args)

        s.group_delete_all()
        
        s.group_define(well, f"all_channels_{well}", list(range(1024)))

        s.start_recording([well])
        
        ############################################################################

        try:
            subprocess.run(program_args)
        except KeyboardInterrupt:
            print("start-maxlab.py: ^C signalled")
        except Exception as err:
            print(err)

        ############################################################################

        s.stop_recording()
        s.stop_file()
        s.group_delete_all()

    print("Experiment complete!")

    for email in emails:
        subprocess.run("./mail.sh", email)
