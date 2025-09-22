# Custom network scan 

import os, sys
import time

import maxlab as mx

top_level_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.append(top_level_dir)

import bin.lib.py_src.hal as hal

# User Input

# metadata 
PLATE_DATE = 0
DIV = 0
CHIP = ''
EXP_ID = 'network scan' # the task 
WELLS = [0,1] # list of wells between 0-5

# saving 
SAVE_DIR = '/home/mxwbio/Desktop/HAL/data/CGRASS' # ex. "/tmp"
H5_FILENAME = 'NSplus_test'

# network scan parameters
REC_LENGTH = 20 # recording length in seconds
REC_ELECS = [[], []]

# logging
DESCRIPTION = ''

if __name__=='__main__':
    
    device = hal.get_system_type()
    if device==0:
        print("MaxOne")
    elif device==1:
        print("MaxTwo")

    # initialize wells 
    for i,well in enumerate(WELLS):
        hal.init_well(well, REC_ELECS[i], stim_elecs=[])
    
    # Assay information
    metadata = {'Plate date' : PLATE_DATE,
                'DIV' : DIV,
                'Chip ID': CHIP,
                'Exp ID' : EXP_ID,
                'Well IDs' : WELLS, 
                'Conditions' :[]} # conditions decoded based on the particular task

    s = mx.Saving() # a single h5 with multiple wells as different groups
    s.open_directory(SAVE_DIR)
    s.start_file(H5_FILENAME)
    s.group_delete_all()

    # Write info to h5 assay/
    hal.write_exp_description(s, DESCRIPTION)
    metadata = hal.write_metadata(s, metadata)

    for well in WELLS:
        s.group_define(well, f"all_channels_{well}", list(range(1024)))

    mx.activate(WELLS) # activate all wells

    s.start_recording(WELLS)

    print("Start recording")
    time.sleep(REC_LENGTH)
    print("Stop recording")

    s.stop_recording()

    time.sleep(mx.Timing.waitAfterRecording)

    s.stop_file()
    s.group_delete_all()




    




