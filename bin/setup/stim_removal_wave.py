#!/usr/bin/env python
from typing import List

from datetime import datetime
import time
import json
import sys
import subprocess
import os
import time

import maxlab as mx

top_level_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.append(top_level_dir)

import bin.gui.GUI as GUI
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

#TODO indicates whether to simply read data, or to stimulate the buttons manually
live_chip = False

#TODO
wells = [0]

# TODO
#
# full path to parent directory of experiment data
#
# data for each trial will be saved in "parent_dir/experiment_name/chip_id/date/trial"
parent_dir = "/home/mxwbio/Desktop/HAL/data/wave-training"

#TODO 
experiment_name = "stim_removal"

#TODO
chip_id = "20551" 

#TODO
maxtwo = False

#TODO 
pre_exp_time = 0
experiment_time = 5
post_exp_time = 0

#TODO
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
desc = f"Removal of noxious stimuli to train burst direction. Stim frequency: {stim_rate} Hz. Threshold: {threshold}. Time: {experiment_time} mins."

#TODO
#
# emails to notify after the experiment ends
emails = []

def get_time():
    return datetime.now().time().strftime("%H:%M")


if __name__ == '__main__':

    trial_path = hal.make_trial_folders_raw(parent_dir, experiment_name, chip_id, wells)

    mx.clear_events() 
    
    for well in wells:
        rec_electrodes = all_configs[well]

        array = hal.init_well(well, rec_electrodes, stim_electrodes[well])

        dir, h5, config_name = hal.get_file_names(well, experiment_name, trial_path)

        array.save_config(config_name)
        
        ############################################################################

        mx.offset()

        single_pulse = Stimulation(f"pulse{well}", 0, 50, 200, 1, 1, 10, 1, well = well)
        duration = single_pulse.get_duration()
        single_pulse.build_sequence(initial_delay = 0)
        
        program_args = [f"./bin/build/new-train-wave", "--config", config_name, "--folder", dir, "--pulse-duration", str(duration)]
        
        if maxtwo:
            program_args.append("--maxtwo")

        #TODO: put them on top to change from run to run
        program_args.append("--threshold")
        program_args.append(str(threshold))
        program_args.append("--minutes")
        program_args.append(str(experiment_time))
        program_args.append("--well")
        program_args.append(str(well))
        program_args.append("--stim-rate")
        program_args.append(str(stim_rate))

        

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

        print(f"{get_time()}: Recording well {well} for {pre_exp_time} minutes...")
        time.sleep(pre_exp_time * 60)

        print(f"Running experiment on well {well}")
        mx.send(mx.Event(well, 1, 1, f"start_experiment {well}"))

        try:
            subprocess.run(program_args)
        except KeyboardInterrupt:
            print("start-maxlab.py: ^C signalled")
        except Exception as err:
            print(err)

        mx.send(mx.Event(well, 1, 2, f"end_experiment {well}"))
        print(f"{get_time()}: Recording well {well} for {post_exp_time} minutes...")

        time.sleep(post_exp_time * 60)

        ############################################################################

        s.stop_recording()
        s.stop_file()
        s.group_delete_all()

    print("Experiment complete!")

    for email in emails:
        subprocess.run("./mail.sh", email)
