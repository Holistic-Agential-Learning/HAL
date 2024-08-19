#!/usr/bin/env python

# m2_stimulation_assay_example
#
# This is a basic example for running custom stimulations on the MaxOne/Two 
# using the HAL helper library.
#  
# Intruction comments for creating your own experiments are dispersed 
# throughout the file and are tagged with '@edit'. Large chunks of code to edit
# begin with a line of '<' characters and end with a line of '>' characters.
#
# Long lines of '#' characters divide major sections of the program
#
# Run with:
#
#       ./m2_stimulation_assay_example.py
#
# Written by Trevor M. Sullivan
# August 19, 2024


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

# @edit
#
# file name of the h5 file where the recording data is stored
file_name = "stimulation_example" 


# @edit
#
# directory to store recording file
recording_dir = "/home/mxwbio/Desktop/HAL/data/stimulation_assay_example"


# @edit
#
# wells to record from (just use 0 if using the MaxOne)
wells = [0] 


# @edit
#
# Modify this to contain the FULL PATH of configs for each well. Just use the 
# first element of the list if using the MaxOne
configs = [
    "/home/mxwbio/Desktop/HAL/test_config_2.cfg", # well 0 config
    "/home/mxwbio/Desktop/HAL/test_config_2.cfg", # well 1 config
    "", # ...
    "",
    "",
    ""
]


# @edit
#
# Modify this to contain the stimulation electrodes for each well. Note that 
# these are electrode numbers (0-26399). Just use the first element of the list 
# if using the MaxOne.
#
# Important note: stimulation electrodes MUST come from the set of recording 
# electrodes defined above. 
stimulation_electrodes = [
    [14915, 14551, 20550], # well 0 stimulation electrodes
    [20590], # well 1 stimulation electrodes
    [], # ... 
    [],
    [],
    []
]

if __name__ == '__main__':

    wells = [0]
    file_name = "open-loop-example"
    chip_id = 16365

    trial_path = hal.make_trial_folders_raw("/home/mxwbio/Desktop/HAL/data/open-loop", file_name, chip_id, wells)

    stim_electrodes = [6630]
    
    for well in wells:
        mx.activate([well])
        mx.set_primary_well(well)
        
        mx.initialize()
        mx.send(mx.Core().enable_stimulation_power(True))
        
        array = mx.Array("stimulation")
        array.reset()
        array.clear_selected_electrodes()

        rec_electrodes = cfg.read_config(configs[well])

        array.select_electrodes(stim_electrodes + rec_electrodes)
        
        array.route()

        # stimulation setup here 
        stimulation_units = hal.connect_stim_units_to_stim_electrodes(stim_electrodes, array)

        directory_name = f"{trial_path}/well{well}"

        config_file_name = directory_name + "/" + file_name + f"_well_{well}_config.cfg"

        #save the config prior to running the code
        array.save_config(config_file_name)

        array.download([well]) 

        mx.offset() 

        mx.clear_events() 

        hal.power_up_stim_units(stimulation_units, 1)

        stimA = Stimulation("A", 1, 10, 500, 10, 1, 1, 1, well = well) 
        stimA.build_sequence()


        ##############################################################################


        s = mx.Saving()
        s.open_directory(directory_name)
        s.start_file(file_name + "_well_" + str(well))
        s.group_delete_all()

        hal.write_exp_description(s, "This is an open-loop example using HAL")
        s.write_assay_property("no_spaces_allowed", "spaces allowed")

        s.group_define(well, f"all_channels_{well}", list(range(1024)))

        s.start_recording([well])

        s.stop_recording()
        s.stop_file()
        s.group_delete_all()
        print("finished recording")
