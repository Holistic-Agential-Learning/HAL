#!/usr/bin/env python

# m2_open_loop_example.py
#
# This was written to do basic conductivity measurements on silk scaffolds
#  
# Important things to check/edit before running each experiment are tagged 
# with TODO
#
# Run with:
#
#       ./ADAM_conductivity.py
#
# Written by Wesley P Clawson
# September 5, 2024


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

import bin.gui.GUI as GUI
from bin.lib.py_src.stimulation import Stimulation
import bin.lib.py_src.hal as hal
import bin.lib.py_src.config as cfg

# TODO
#
# experiment name
experiment_name = "conductivity-test-CNTsilk-PEDOTPSS-1.0p" #-low-amp


# TODO
#
# directory to store the experiment data
parent_dir = "/home/mxwbio/Desktop/HAL/data/adam_conductivity"


# TODO
#
# wells to record from (just use 0 if using the MaxOne)
wells = [0] 

# TODO
#
# chip ID
chip_id = 20660

# CHIP silences
# 20660 - 481,552,449 -0> 475,725,662,481
# 20439 - 486,656
# 20458 - 373,374,300


# TODO
#
# Modify this to contain the full path of configs for each well. Just use the 
# first element of the list if using the MaxOne
configs = [
    "/home/mxwbio/configs/240905/Puck_config.cfg", # well 0 config
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
    [13703], # do some on left
    [], # well 1 stimulation electrodes
    [], # ... 
    [],
    [],
    []
]

if __name__ == '__main__':
    trial_path = hal.make_trial_folders_raw(parent_dir, experiment_name, chip_id, wells)
    
    for well in wells:
        config_elecs = cfg.read_config_elecs(configs[well])
        #sq0 = hal.get_electrode_square(5000, 6, 1)
        #sq1 = hal.get_electrode_square(10000, 5, 2)

        rec_elecs = config_elecs + stim_elecs[well] # + sq0 + sq1 if needed
        
        # If the last two arguments are not supplied, this function will 
        # automatically connect and power up the stimulation units on DAC 0. 
        # If you need to have stimulations on different DAC channels, it's 
        # better to manually do it yourself. 
        array = hal.init_well(well, rec_elecs, stim_elecs[well], False, False)

        stim_units_0 = hal.connect_stim_units_to_stim_electrodes(stim_elecs[well],  array)

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

        # 200 and 650 // 10 and 50
        stim_a_obj = Stimulation("A-200mv", dac_source=0, amplitude=200, phase=200, 
                            pulses_per_train=10, num_trains=2, pulse_interval=100, 
                            pulse_train_interval=1, well=well)
        stim_a_dur = stim_a_obj.duration

        stim_a = stim_a_obj.build_sequence()
        
        stim_b_obj = Stimulation("B-650mv", dac_source=0, amplitude=650, phase=200, 
                            pulses_per_train=10, num_trains=2, pulse_interval=100, 
                            pulse_train_interval=1, well=well)
        stim_b_dur = stim_b_obj.duration

        stim_b = stim_b_obj.build_sequence()


        stim_c_obj = Stimulation("C-10mv", dac_source=0, amplitude=10, phase=200, 
                            pulses_per_train=10, num_trains=2, pulse_interval=100, 
                            pulse_train_interval=1, well=well)
        stim_c_dur = stim_c_obj.duration

        stim_c = stim_c_obj.build_sequence()
        
        stim_d_obj = Stimulation("D-50mv", dac_source=0, amplitude=50, phase=200, 
                            pulses_per_train=10, num_trains=2, pulse_interval=100, 
                            pulse_train_interval=1, well=well)
        stim_d_dur = stim_d_obj.duration

        stim_d = stim_d_obj.build_sequence()

        ########################################################################

        s = mx.Saving()
        s.open_directory(rec_dir)
        s.start_file(h5_name)
        s.group_delete_all()
        
        try:

            # these functions write data directly to the h5 file, found under the
            # "assay" section
            hal.write_exp_description(s, "This is an open-loop example using HAL")
            hal.write_stim_electrodes(s, stim_elecs[well])
            s.write_assay_property("no_spaces_allowed", "spaces allowed")

            s.group_define(well, f"all_channels_{well}", list(range(1024)))

            s.start_recording([well])
            print("Started recording ...")

            print("5 sec pause")
            time.sleep(5)

            print("Sending 200mv sequence...")
            stim_a.send()
            time.sleep(stim_a_dur)

            print("5 sec pause")
            time.sleep(5)

            print("Sending 650mv sequence...")
            stim_b.send()
            time.sleep(stim_b_dur)

            print("10 sec pause")
            time.sleep(10)

            print("Sending 10mv sequence...")
            stim_c.send()
            time.sleep(stim_c_dur)

            print("5 sec pause")
            time.sleep(5)

            print("Sending 50mv sequence...")
            stim_d.send()
            time.sleep(stim_d_dur)

            print("5 sec pause")
            time.sleep(5)
            
        except KeyboardInterrupt:
            print(f"{__file__}: keyboard interrupt detected")
        except Exception as err:
            print(f"{__file__}: an error was detected (reason: {err})")

        s.stop_recording()
        s.stop_file()
        s.group_delete_all()
        print("finished recording")
