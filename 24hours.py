#!/usr/bin/env python
from typing import List


import random
import time
import json
import sys
import subprocess
import os
import datetime

import maxlab as mx

import bin.gui.GUI as GUI
from bin.lib.py_src.stimulation import Stimulation
import bin.lib.py_src.hal as hal

parent_path = "/home/mxwbio/Desktop/HAL/data/24-hour-recordings"
experiment_name = "NeuroDev_Test1"
chip_id = 25269
notes = "Syd plated this one. We're testing to see if we can see the development over time. DIV0 to DIV10"
config_path = "/home/mxwbio/configs/240815/25269D6.cfg"

# function for reading in electrode numbers from a config
def get_config_electrodes(config_file):
    file = open(config_file, "r")
    contents = file.read()
    electrode_nums = []
    curr_word = ''

    for char in contents:
        # character before electrode number
        if (char == '('):
            curr_word = ''

        # character after electrode number
        elif (char == ')'):
            electrode_nums.append(int(curr_word))
            curr_word = ''
        
        # all electrodes have been processed
        elif (char == 'H'):
            break
        else:                                                                       
            curr_word = curr_word + char
    
    file.close()
    
    return electrode_nums


if __name__ == '__main__':

    trial_path = hal.make_trial_folders_raw(parent_path, experiment_name, chip_id, [0])

    mx.clear_events() 

    mx.initialize()

    mx.activate([0])
    
    array = mx.Array(f"recording")
    array.reset()
    array.clear_selected_electrodes()
    
    # array.load_config(config_path)
    recording_electrodes = get_config_electrodes(config_path)
    array.select_electrodes(recording_electrodes)

    array.route()

    array.download([0])

    recording_dir = trial_path + "/well0"

    array.save_config(f"{recording_dir}/{experiment_name}_well_0_config.cfg")

    mx.offset()

    # loop
    for i in range(24):
        recording_file = f"{experiment_name}_{i}"
        

        s = mx.Saving()
        s.open_directory(recording_dir)

        try:
            s.start_file(recording_file)

            #Write metadata
            now = datetime.datetime.now()
            hal.write_exp_description(s, f"Hour {i}, recorded at {now.time()}")
            s.write_assay_property("Notes", notes)

            s.group_delete_all()
            
            s.group_define(0, f"all_channels_{0}", list(range(1024)))

            
            print(f"Hour {i} ({now.time()}): recording")
            s.start_recording([0])
            
            time.sleep(900)

            
        except KeyboardInterrupt:
            print("^C signalled")
            s.stop_recording()
            s.stop_file()
            s.group_delete_all()

        s.stop_recording()
        s.stop_file()
        s.group_delete_all()
        now = datetime.datetime.now()
        print(f"Hour {i} ({now.time()}): sleeping")
        time.sleep(2700)

    subprocess.run(["./mail.sh"])
