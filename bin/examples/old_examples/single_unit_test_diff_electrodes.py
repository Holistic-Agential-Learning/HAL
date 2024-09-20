#!/usr/bin/env python

import maxlab as mx

from typing import List
from time import sleep
from h5py import File

import json

import sys
import os
import csv
sys.path.append(os.path.dirname(__file__) + "/../..")
import bin.lib.py_src.hal as hal
from bin.lib.py_src.stimulation import Stimulation


################################################################################
# GLOBAL VARIABLES

# @edit
#
# file name of the h5 file where the recording data is stored
file_name = "single_unit_stimulation_different_electrodes" 


# @edit
#
# directory to store recording file
recording_dir = "/home/mxwbio/Desktop/HAL/data/single_unit/different_electrodes/"


# @edit
#
# wells to record from (just use 0 if using the MaxOne)
wells = range(6) #, 1, 2, 3, 4, 5] 


# @edit
#
# Modify this to contain the FULL PATH of configs for each well. Just use the 
# first element of the list if using the MaxOne

configs = [
    "/home/mxwbio/configs/240813/13h46m02s.cfg",
    "/home/mxwbio/configs/240813/13h46m05s.cfg",
    "/home/mxwbio/configs/240813/13h46m08s.cfg",
    "/home/mxwbio/configs/240813/13h46m13s.cfg",
    "/home/mxwbio/configs/240813/13h46m16s.cfg",
    "/home/mxwbio/configs/240813/13h46m21s.cfg"
]


# @edit
#
# Modify this to contain the stimulation electrodes for each well. Note that 
# these are electrode numbers (0-26399). Just use the first element of the list 
# if using the MaxOne.
#
# Important note: stimulation electrodes MUST come from the set of recording 
# electrodes defined above. 
stimulation_electrodes = [18714, 7192, 4815, 10138, 11267, 9057] # well 1 stimulation electrodes
#     [13310], # well 2 stimulation electrodes
#     [13310], # well 3 stimulation electrodes 
#     [13310], # well 4 stimulation electrodes
#     [13310], # well 5 stimulation electrodes
#     [13310]  # well 6 stimulation electrodes
# ]


all_stim_electrodes = list()
for center_stim_elec in stimulation_electrodes:
    well_stim_elecs = list()
    for i in range(center_stim_elec - 220 * 2, center_stim_elec + 220 * 3, 220 * 2):
            for j in range(i - 2, i + 3, 2):
                well_stim_elecs.append(j)
    
    all_stim_electrodes.append(well_stim_elecs)

################################################################################
# HELPER FUNCTIONS

# function for connecting stimulation units to stimulation electrodes
def connect_stim_units_to_stim_electrodes(
    stim_electrodes: List[int], array: mx.Array
) -> List[int]:
    stim_units: List[int] = []
    for stim_el in stim_electrodes:
        array.connect_electrode_to_stimulation(stim_el)
        stim = array.query_stimulation_at_electrode(stim_el)
        if len(stim) == 0:
            raise RuntimeError(
                f"No stimulation channel can connect to electrode: \
                    {str(stim_el)}"
            )
        stim_unit_int = int(stim)
        if stim_unit_int in stim_units:
            raise RuntimeError(
                f"Two electrodes connected to the same stim unit. This is not \
                  allowed. Please Select a neighboring electrode of {stim_el}!"
            )
        else:
            stim_units.append(stim_unit_int)
    return stim_units

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

################################################################################
# MAIN
#
if __name__ == "__main__":
    ############################################################################
    # SETUP EXPERIMENT
    mx.initialize()
    sleep(5)
    if mx.send(mx.Core().enable_stimulation_power(True)) != "Ok":
        raise RuntimeError("The system didn't initialize correctly.")
    sleep(mx.Timing.waitInit)

    mx.clear_events()

    print("Making stimulations...")

    #<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
    
    pulse = Stimulation(f"pulse", 0, 360, 200, 1, 1, 1, 1)

    pulse_seq = pulse.build_sequence()
    ############################################################################
    # RUN EXPERIMENT
    for stim_elec_no in range(9):
        #power on appropriate stim unit
        print("Stim electrode no " + str(stim_elec_no))

        for well in wells:
            hal.init_well(well, get_config_electrodes(configs[well]), [all_stim_electrodes[well][stim_elec_no]], connect = True, power_up = True)

        sleep(mx.Timing.waitAfterDownload)

        mx.activate(wells)
        mx.offset()
        sleep(15)






        s = mx.Saving()
        s.open_directory(recording_dir)
        s.start_file(file_name + f"_stim_elec_{stim_elec_no}")

        for well in wells:
            s.group_define(well, f"all_channels_{well}", list(range(1024)))

            stim_elecs = [all_stim_electrodes[well][stim_elec_no]]

            s.write_assay_property(f"stim_elecs_{well}", ", ".join(str(x) for x in stim_elecs))
        
        s.start_recording(wells)

        sleep(20)

        for i in range(30):
            print("Pulse no " + str(i))
            pulse_seq.send()
            sleep(4)
        
        # end of recording
        #>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
        
        # stop recording
        s.stop_recording()
        sleep(mx.Timing.waitAfterRecording)
        s.stop_file()
        s.group_delete_all()
    
