#!/usr/bin/env python
from typing import List


import random
import time
import json
import sys
import subprocess
import os



import maxlab as mx

import bin.gui.GUI as GUI
from bin.lib.py_src.stimulation import Stimulation
import bin.lib.py_src.hal as hal

PARENT_PATH = "/home/mxwbio/Desktop/HAL/data/24-hour-recordings"
EXPERIMENT_NAME = "maxtwo-plates"
CHIP_ID = 123456
NOTES = """
Add your notes here"""

config = "config"




if __name__ == '__main__':

    trial_path = hal.make_trial_folders_raw()
        


    mx.clear_events() 
    
    well_data = {}
    mx.activate([0])

    mx.initialize()
    mx.send(mx.Core().enable_stimulation_power(True))

    # stimulation electrodes for configs/newconfig.cfg
    
    array = mx.Array(f"recording")
    array.reset()
    array.clear_selected_electrodes()
    
    array.select_config()
    
    array.route()

    array.download([0])

    recording_dir = trial_path + "/well0"

    array.save_config()

    mx.offset()

    # loop
    hour = 0
    recording_file = f"{EXPERIMENT_NAME}_{hour}"
    
    s = mx.Saving()
    s.open_directory(recording_dir)
    s.start_file()

    #Write metadata
    hal.write_exp_description(s, "")

    s.group_delete_all()
    
    s.group_define(0, f"all_channels_{0}", list(range(1024)))

    print("recording... 0 " + str(0))
    s.start_recording([0])

    s.stop_recording()
    s.stop_file()
    s.group_delete_all()
    print("finished recording")
