# Custom network scan 

import os, sys
import time

import maxlab as mx

top_level_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.append(top_level_dir)

import bin.lib.py_src.hal as hal

# User Input
wells = [0,1] # list of wells between 0-5
path_to_config = '' # full path to MaxWell configuration file
save_dir = '' # ex. "/tmp"
h5_filename = 'NSplus_test'
rec_length = 20 # recording length in seconds

if __name__=='__main__':

    # initialize wells 
    hal.init_wells(wells, rec_elecs=path_to_config, stim_elecs=[])

    s = mx.Saving() # a single h5 with multiple wells as different groups
    s.open_directory(save_dir)
    s.start_file(h5_filename)
    s.group_delete_all()

    for well in wells:
        s.group_define(well, f"all_channels_{well}", list(range(1024)))

    s.start_recording(wells)

    print("Start recording")
    time.sleep(rec_length)
    print("Stop recording")

    s.stop_recording()

    time.sleep(mx.Timing.waitAfterRecording) #NOTE: Is this necessary?

    s.stop_file()
    s.group_delete_all()




    




