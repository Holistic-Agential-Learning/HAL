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
wells = [0, 1, 2, 3, 4, 5] 

# TODO
#
# chip ID
chip_id = 7480

# TODO - WES
#
# Modify this to contain the FULL PATH of configs for each well. Just use the 
# first element of the list if using the MaxOne
configs = [
    "/home/mxwbio/configs/240822/12h48m32s.cfg", # well 0 config
    "/home/mxwbio/configs/240822/12h48m36s.cfg", # well 1 config
    "/home/mxwbio/configs/240822/12h48m39s.cfg", # ...
    "/home/mxwbio/configs/240822/12h48m42s.cfg",
    "/home/mxwbio/configs/240822/12h48m45s.cfg",
    "/home/mxwbio/configs/240822/12h48m47s.cfg"
]

# TODO
#
# Modify this to contain the stimulation electrodes for each well. Note that 
# these are electrode numbers (0-26399). Just use the first element of the list 
# if using the MaxOne.
#
# Important note: stimulation electrodes MUST come from the set of recording 
# electrodes defined above. 

# GOAL - LOOP OVER EVERY ELECTRODE WE WANT TO EXAMINE

# First three are excite, second 3 are inhib
total_electrode_list = [
    [21531, 22855, 25903, 7455, 6385, 21415], # well 0 stimulation electrodes
    [3745, 4631, 13015,26203, 7913, 9933], # well 1 stimulation electrodes
    [4381, 9671, 6143,22663, 17423, 20941], # ... 
    [24031, 22393, 14911,4691, 19741, 20215],
    [1151, 9483, 10795, 1609, 12701, 419],
    [25951, 17999, 22671,10045, 6501, 5595]
]

if __name__ == '__main__':

    trial_path = hal.make_trial_folders_raw(parent_dir, experiment_name, chip_id, wells)

    for stim_idx, _ in enumerate(total_electrode_list[0]):
        for well in wells:  
            electrode = total_electrode_list[well][stim_idx]

            print("elec: " + str(electrode) + " on well: " + str(well))

            config_elecs = GUI.read_config(configs[well], False)[1]

            stim_square = hal.get_electrode_square(electrode, 4, 1)  # TODO

            rec_elecs = stim_square + config_elecs
            
            array = hal.init_well(well, rec_elecs, [electrode], False, False)

            stim_units_0 = hal.connect_stim_units_to_stim_electrodes([electrode],  array)    # TODO

            # init_well automatically does this--this is only needed when 
            # manually connecting stimulation units, as shown above
            array.download()
            mx.offset()

            # power up each set of stimulation units separately, choosing a 
            # different DAC channel for each
            hal.power_up_stim_units(stim_units_0, dac=0)

            _, _, config = hal.get_file_names(well, experiment_name, trial_path)

            #save the config prior to running the code
            array.save_config(config)

        h5_name =  experiment_name + "_" + str(stim_idx)
        rec_dir = trial_path

        # TODO - dac source must match the dac from power_up_stim_units
        stim = Stimulation("A", dac_source=0, amplitude=250, phase=200, 
                            pulses_per_train=10, num_trains=1, pulse_interval=1000, 
                            pulse_train_interval=5, well=0) 
        stim_duration = stim.duration
        stim_seq = stim.build_sequence()

        ########################################################################

        s = mx.Saving()
        s.open_directory(rec_dir)
        s.start_file(h5_name)
        s.group_delete_all()

        # these functions write data directly to the h5 file, found under the
        # "assay" section
        hal.write_exp_description(s, "Running single unit stim in parallel for 3 excite and 3 inhib.")  # TODO
        hal.write_stim_electrodes(s, [elecs[stim_idx] for elecs in total_electrode_list])

        for well in wells:
            s.group_define(well, f"all_channels_{well}", list(range(1024)))

        s.start_recording(wells)
        try:

            time.sleep(5)
            
            mx.activate(wells)

            print("Ready to rumble")
            # TODO
            time.sleep(60)  # Pre stim test
            print("Sending first sequence")
            stim_seq.send()
            time.sleep(stim_duration)
            time.sleep(60)  # post stim test
            print("End of post, beginning the next pretest...")

            time.sleep(60)  # Pre stim test
            print("Sending second sequence")
            stim_seq.send()
            time.sleep(stim_duration)
            time.sleep(60)  # Pre stim test
        except KeyboardInterrupt:
            print("Keyboard interrupt detected")
        except Exception as err: 
            print(f"An error occurred ({err})")

        s.stop_recording()
        s.stop_file()
        s.group_delete_all()
        print("finished recording location " + str(stim_idx) + " of 6")
