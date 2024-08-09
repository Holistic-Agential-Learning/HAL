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
experiment_name = "test"
chip_id = 123456

config_path = "/home/mxwbio/Desktop/HAL/test_config_2.cfg"




if __name__ == '__main__':

    trial_path = hal.make_trial_folders_raw(parent_path, experiment_name, chip_id, [0])

    mx.clear_events() 
    
    mx.activate([0])

    mx.initialize()
    mx.send(mx.Core().enable_stimulation_power(True))
    
    array = mx.Array(f"recording")
    array.reset()
    array.clear_selected_electrodes()
    
    array.load_config(config_path)
    
    array.route()

    array.download([0])

    recording_dir = trial_path + "/well0"

    array.save_config(f"{recording_dir}/{experiment_name}_well_0_config.cfg")

    mx.offset()

    # loop
    for i in range(2):
        recording_file = f"{experiment_name}_{i}"
        
        s = mx.Saving()
        s.open_directory(recording_dir)
        s.start_file(recording_file)

        #Write metadata
        now = datetime.datetime.now()
        hal.write_exp_description(s, f"Hour {i}, recorded at {now.time()}")

        s.group_delete_all()
        
        s.group_define(0, f"all_channels_{0}", list(range(1024)))

        
        print(f"Hour {i} ({now.time()}): recording")
        s.start_recording([0])
        
        time.sleep(900)

        s.stop_recording()
        s.stop_file()
        s.group_delete_all()

        now = datetime.datetime.now()
        print(f"Hour {i} ({now.time()}): sleeping")
        time.sleep(2700)

    subprocess.run(["./mail.sh"])
