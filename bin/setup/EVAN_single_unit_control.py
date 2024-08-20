#!/usr/bin/env python

# TODO
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

import time
import json
import sys
import os

top_level_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.append(top_level_dir)

import maxlab as mx

import bin.gui.GUI as GUI
from bin.lib.py_src.stimulation import Stimulation
import bin.lib.py_src.hal as hal
import bin.lib.py_src.config as cfg

# TODO
#
# experiment name
experiment_name = "single_unit_control"

# TODO
#
# directory to store the experiment data
parent_dir = "/home/mxwbio/Desktop/HAL/data/evan/"

# TODO
#
# wells to record from (just use 0 if using the MaxOne)
wells = [0] 

# TODO
#
# chip ID
chip_id = 7480


# TODO - WES
#
# Modify this to contain the FULL PATH of configs for each well. Just use the 
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
# these are electrode numbers (0-26399). Just use the first element of the list 
# if using the MaxOne.
#
# Important note: stimulation electrodes MUST come from the set of recording 
# electrodes defined above. 
stim_elecs = [
    [5000, 10000], # well 0 stimulation electrodes
    [], # well 1 stimulation electrodes
    [], # ... 
    [],
    [],
    []
]

# GOAL - LOOP OVER EVERY ELECTRODE WE WANT TO EXAMINE

stim_excitatory = [ ]   # TODO  SHOULD BE LIST OF ELECTRODES
stim_inhibitory = [ ]   # TODO

for ELECTRODE in oawnefoiajfeoie:
    if __name__ == '__main__':
        trial_path = hal.make_trial_folders_raw(parent_dir, experiment_name, chip_id, wells)
        
        for well in wells:
            config_elecs = cfg.read_config(configs[well])

            stim_square = hal.get_electrode_square(ELECTRODE, 3, 1)  # TODO

            rec_elecs = stim_square + config_elecs
            
            array = hal.init_well(well, rec_elecs, stim_elecs, False, False)

            stim_units_0 = hal.connect_stim_units_to_stim_electrodes([ELECTRODE],  array)    # TODO

            # init_well automatically does this--this is only needed when 
            # manually connecting stimulation units, as shown above
            array.download()
            mx.offset()

            # power up each set of stimulation units separately, choosing a 
            # different DAC channel for each
            hal.power_up_stim_units(stim_units_0, dac=0)

            rec_dir, h5_name, config = hal.get_file_names(well, experiment_name, trial_path)

            #save the config prior to running the code
            array.save_config(config)

            
            # TODO - dac source must match the dac from power_up_stim_units
            stimA = Stimulation("A", dac_source=0, amplitude=250, phase=200, 
                                pulses_per_train=10, num_trains=1, pulse_interval=1, 
                                pulse_train_interval=1, well=well) 
            stim_duration = stimA.duration
            stimA.build_sequence()

            ########################################################################

            s = mx.Saving()
            s.open_directory(rec_dir)
            s.start_file(h5_name)
            s.group_delete_all()

            # these functions write data directly to the h5 file, found under the
            # "assay" section
            hal.write_exp_description(s, "This is an open-loop example using HAL")  # TODO
            hal.write_stim_electrodes(s, stim_elecs[well])
            s.write_assay_property("no_spaces_allowed", "spaces allowed")
            s.write_assay_property("what_i_had_for_lunch", "thai food")

            s.group_define(well, f"all_channels_{well}", list(range(1024)))

            s.start_recording([well])

            time.sleep(5)
            
            # TODO
            stimA.send()
            time.sleep(stim_duration)

            time.sleep(60)

            stimA.send()
            time.sleep(stim_duration)

            time.sleep(60)

            s.stop_recording()
            s.stop_file()
            s.group_delete_all()
            print("finished recording")
