#!/usr/bin/env python

# 24hours.py
#
# This script will run for 24 hours and record for 15 minutes every hour. This 
# can be configured to different times, but it allows us to track a culture's
# development without outputting too much data. Intended to run on the MaxOne.
#
# Variables to check before running are tagged with TODO
#
# Written by Trevor M. Sullivan
# August, 2024


import time
import subprocess
import datetime

import maxlab as mx

import bin.lib.py_src.hal as hal


# TODO
#
# full path to parent directory of experiment data
#
# data for each trial will be saved in "parent_dir/experiment_name/chip_id/date/trial"
parent_path = "/home/mxwbio/Desktop/HAL/data/24-hour-recordings"

# TODO 
experiment_name = "NeuroDev_Test1"

# TODO
chip_id = 25269

# TODO
notes = "Syd plated this one. We're testing to see if we can see the development over time. DIV0 to DIV10"

# TODO
config_path = "/home/mxwbio/configs/240815/25269D6.cfg"

# TODO
#
# number of hours to run the script for
num_hours = 24

# TODO
#
# time to record starting at the beginning of each hour, in minutes
# must be less than 60
record_time = 15

# TODO
emails = ["trevor.sullivan@tufts.edu"]


if __name__ == '__main__':
    
    trial_path = hal.make_trial_folders_raw(parent_path, experiment_name, chip_id, [0])

    array = hal.init_well(0, config_path, [])

    recording_dir, _, config_name = hal.get_file_names(0, experiment_name, trial_path)
    
    array.save_config(config_name)

    for i in range(num_hours):
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

            
            print(f"Hour {i} ({now.time()}): recording; {num_hours - i} hours remaining")
            s.start_recording([0])
            
            time.sleep(record_time * 60)

            
        except KeyboardInterrupt:
            print("^C signalled")
            s.stop_recording()
            s.stop_file()
            s.group_delete_all()

        s.stop_recording()
        s.stop_file()
        s.group_delete_all()
        now = datetime.datetime.now()
        print(f"Hour {i} ({now.time()}): sleeping; {num_hours - i - (record_time / 60)} hours remaining")

        # sleep for the rest of the hour
        time.sleep((60 - record_time) * 60)
    
    subprocess.run(["./mail.sh"] + emails)
