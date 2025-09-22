# Custom network scan 

import os, sys
import time

import maxlab as mx

top_level_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.append(top_level_dir)

import bin.lib.py_src.hal as hal
import bin.lib.py_src.electrode_selection as es

# User Input

# metadata 
PLATE_DATE = 250828
DIV = 25
CHIP = 'P004028'
EXP_ID = 'network scan' # the task 
WELLS = [0] # list of wells between 0-5

# saving 
SAVE_DIR = '/home/mxwbio/Data/Batch_1_-_Fall_2025_MaxOne/250922/P004028/NetworkScan' # ex. "/tmp"
H5_FILENAME = 'NSplus_test'

# network scan parameters
REC_LENGTH = 60 # recording length in seconds
PATH_TO_AS = '/home/mxwbio/Data/Batch_1_-_Fall_2025_MaxOne/250922/P004028/ActivityScan/000020/data.raw.h5' # this holds the activity scan data for all wells for the specified chip
REC_ELECS = None # dictionary {well:[recording_electrodes]}

# logging
DESCRIPTION = 'Testing AS->NS pipeline and metadata'

if __name__=='__main__':

    os.makedirs(SAVE_DIR, exist_ok=True)
    
    device = hal.get_system_type()
    if device==0:
        print(device, "MaxOne")
    else:
        print(device, "MaxTwo")

    if REC_ELECS is None and PATH_TO_AS!='':
        # Determine recording electrodes from activity scans
        REC_ELECS = es.select_electrodes(PATH_TO_AS, SAVE_DIR)

    # initialize wells 
    for well in WELLS:
        hal.init_well(well, REC_ELECS[well], stim_elecs=[])
    
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




    




