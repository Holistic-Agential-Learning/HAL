#!/usr/bin/env python

# m2_open_loop_example.py
#
# This is a basic example for running custom stimulations on the MaxOne/Two 
# using the HAL helper library.
#  
# Important things to check/edit before running each experiment are tagged 
# with TODO
#
# Run with:
#
#       ./m2_open_loop_example.py
#
# Written by Trevor M. Sullivan
# September 2024


from typing import List

import random
import time

import json
import sys
import subprocess
import os

top_level_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.append(top_level_dir)

import maxlab as mx

from punish_reward.macro_punish import macro_punish
from punish_reward.macro_reward import macro_reward
from punish_reward.sine_reward import sine_reward

import bin.gui.GUI as GUI
from bin.lib.py_src.stimulation import Stimulation
import bin.lib.py_src.hal as hal
import bin.lib.py_src.config as cfg

# TODO
#
# experiment name
experiment_name = "open-loop-example"


# TODO
#
# directory to store the experiment data
parent_dir = "/home/mxwbio/Desktop/HAL/data/open-loop"


# TODO
#
# wells to record from (use 0 if using the MaxOne)
wells = [0] 

# TODO
#
# chip ID
chip_id = 16365


# TODO
#
# Modify this to contain the full path of configs for each well. Use the 
# first element of the list if using the MaxOne
configs = [
    "/home/mxwbio/Desktop/HAL/test_config_2.cfg", # well 0 config
    "", # well 1 config
    "", # ...
    "",
    "",
    ""
]


# TODO
#
# Modify this to contain the stimulation electrodes for each well. Note that 
# these are electrode numbers (0-26399). Use the first element of the list 
# if using the MaxOne. 
#
# Important note: stimulation electrodes MUST be included as recording 
# electrodes--they are automatically added below
stim_elecs = [
    [5000, 10000], # well 0 stimulation electrodes
    [], # well 1 stimulation electrodes
    [], # ... 
    [],
    [],
    []
]

if __name__ == '__main__':

    # create folders to save experiment data
    trial_path = hal.make_trial_folders_raw(parent_dir, experiment_name, chip_id, wells)

    for well in wells:
        rec_elecs = cfg.read_config_elecs(configs[well])
        stim_squares = []

        # make 5x5 (2 steps from center) squares around stimulation electrodes
        for electrode in stim_elecs[well]:
            stim_squares += hal.get_electrode_square(electrode, 2)
        
        rec_elecs += stim_squares

        # upload configuration electrodes, connect and power up stimulation electrodes
        array = hal.init_well(well, rec_elecs, stim_elecs[well])

        # get the paths of relevant files
        rec_dir, h5_name, config = hal.get_file_names(well, experiment_name, trial_path)

        # save the config prior to running the experiment
        array.save_config(config)

        # create stimulations
        stim_a_obj = Stimulation("A", dac_source=0, amplitude=10, phase=500, 
                            pulses_per_train=10, num_trains=1, pulse_interval=1, 
                            pulse_train_interval=1, well=well)
        stim_a = stim_a_obj.build_sequence()

        stim_b_obj = Stimulation("B", dac_source=0, amplitude=20, phase=500, 
                            pulses_per_train=10, num_trains=1, pulse_interval=1, 
                            pulse_train_interval=1, well=well)
        stim_b = stim_b_obj.build_sequence()


        ########################################################################


        s = mx.Saving()
        s.open_directory(rec_dir)
        s.start_file(h5_name)
        s.group_delete_all()

        # these functions write data directly to the h5 file, found under the
        # "assay" section
        hal.write_exp_description(s, "This is an open-loop example using HAL")
        hal.write_stim_electrodes(s, stim_elecs[well])
        s.write_assay_property("no_spaces_allowed", "spaces allowed")

        s.group_define(well, f"all_channels_{well}", list(range(1024)))

        s.start_recording([well])

        time.sleep(5)

        stim_a.send()

        time.sleep(5)

        stim_b.send()

        time.sleep(5)

        stim_a.send()
        stim_b.send()

        time.sleep(5)

        s.stop_recording()
        s.stop_file()
        s.group_delete_all()
        print("finished recording")
