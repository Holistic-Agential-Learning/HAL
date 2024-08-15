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
recording_dir = "/home/mxwbio/Desktop/HAL/data/single_unit/"


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
    for i in range(center_stim_elec - 220 * 3, center_stim_elec + 220 * 4, 220):
            for j in range(i - 3, i + 4):
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

    print("Initializing wells...")

    all_arrays = [0] * 6

    # sets up recording and stimulation electrodes for each well
    for well in wells:

        print(f"Setting up well {well}...")

        # activate the current well
        mx.activate([well])
        mx.set_primary_well(well)

        # get config file and recording electrode numbers
        config_file = configs[well]
        config_file = configs[well]
        recording_electrodes = get_config_electrodes(config_file)
        #recording_electrodes = configs[well] 

        # grab the stimulation electrodes
        stim_elecs = all_stim_electrodes[well]

        print(f"Stimulation electrodes: {stim_elecs}")

        array = mx.chip.Array(f"stimulation{well}")

        # set recording and stimulation electrodes
        #
        # Note: stimulation electrodes must also be recording electrodes
        #array.reset()
        array.clear_selected_electrodes( )
        #for row in range(stim_elecs[0] - 220 * 10, stim_elecs[0] + 220 * 11, 220):
        #    array.select_electrodes(range(row - 10, row + 11), 2)
        
        array.select_stimulation_electrodes(stim_elecs)
        array.select_electrodes(recording_electrodes)
        array.route()

        # connect stimulation units
        stimulation_units = hal.connect_stim_units_to_stim_electrodes(
            stim_elecs, array
        )

        # download data to the well
        array.download([well])
        all_arrays[well] = array

    mx.activate(wells)

    print("Offsetting...")
    sleep(mx.Timing.waitAfterDownload)
    mx.offset()
    sleep(15)

    mx.clear_events()

    print("Making stimulations...")

    #<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
    
    pulse = Stimulation(f"pulse", 0, 360, 200, 1, 1, 1, 1)

    pulse_seq = pulse.build_sequence()
    ############################################################################
    # RUN EXPERIMENT

    s = mx.Saving()
    s.open_directory(recording_dir)
    s.start_file(file_name)

    for well in wells:
        s.group_define(well, f"all_channels_{well}", list(range(1024)))

        stim_elecs = all_stim_electrodes[well]

        s.write_assay_property(f"stim_elecs_{well}", ", ".join(str(x) for x in stim_elecs))

    s.start_recording(wells)

    
    #<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
    # @edit
    #
    # Send stimulations and configure experiment timings here

    print("Starting recording...")
    sleep(5)


    for stim_elec_no in range(9):
        #power on appropriate stim unit
        print("Stim electrode no " + str(stim_elec_no))
        mx.send(mx.Event(0, 1, stim_elec_no + 10, f"stim_elec_no {stim_elec_no}"))
        for well in wells:
            stim_elec = all_stim_electrodes[well][stim_elec_no]

            stim_unit = all_arrays[well].query_stimulation_at_electrode(stim_elec)
            # power up stimulation units
            mx.activate([well])
            mx.send(
                mx.StimulationUnit(stim_unit)
                .power_up(True)
                .connect(True)
                .set_voltage_mode()
                .dac_source(0)
            )

        mx.activate(wells)
        for i in range(30):
            pulse_seq.send()
            sleep(4)


        #power off
        for stim_unit in range(0, 32):
            mx.send(
                mx.StimulationUnit(stim_unit)
                .power_up(False)
            )

    

    # end of recording
    #>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    
    # stop recording
    s.stop_recording()
    sleep(mx.Timing.waitAfterRecording)
    s.stop_file()
    s.group_delete_all()
    
