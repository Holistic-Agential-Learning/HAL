#!/usr/bin/env python

# m2_stimulation_assay_example
#
# This is an open loop testing script that should stimulate all 6 wells at various frequencies, 
# at varying amplitudes on a blank chip, to get a baseline level of stimulation artifact. 
# Chips should not have water in them, but CMM. 
#
# Run with:
#
#       ./m2_stim_artifact_testing.py
#
# Written by Wesley P. Clawson
# August 5, 2024

# This was copied from 'other files - I think should let me use HAL.py'

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
file_name = "stimulation_artifact_test_fix" 


# @edit
#
# directory to store recording file
recording_dir = "/home/mxwbio/Desktop/HAL/data/testing/"


# @edit
#
# wells to record from (just use 0 if using the MaxOne)
wells = [0] #, 1, 2, 3, 4, 5] 


# @edit
#
# Modify this to contain the FULL PATH of configs for each well. Just use the 
# first element of the list if using the MaxOne

with open("/home/mxwbio/Desktop/HAL/Ephaptic/configs/caspfiguration_center.txt", 'r') as f:
    center_config = [int(row[0]) for row in csv.reader(f, delimiter='\t')]


configs = [center_config] # well 0 config
#     center_config, # well 1 config
#     center_config, # well 2 config
#     center_config, # well 3 config
#     center_config, # well 4 config
#     center_config, # well 5 config
# ]


# @edit
#
# Modify this to contain the stimulation electrodes for each well. Note that 
# these are electrode numbers (0-26399). Just use the first element of the list 
# if using the MaxOne.
#
# Important note: stimulation electrodes MUST come from the set of recording 
# electrodes defined above. 
stimulation_electrodes = [[13310]] # well 1 stimulation electrodes
#     [13310], # well 2 stimulation electrodes
#     [13310], # well 3 stimulation electrodes 
#     [13310], # well 4 stimulation electrodes
#     [13310], # well 5 stimulation electrodes
#     [13310]  # well 6 stimulation electrodes
# ]


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

# parses json that was created with the GUI
def parse_json(json_name):
    global file_name, recording_dir, wells, configs
    f = open(json_name, "r")
    params = json.load(f)
    f.close()

    wells = params['WELLS']

    file_name = params['NAME']
    recording_dir = params['FOLDER']

    for well in wells:
        configs[well] = params['CONFIGS'][str(well)]['PATH']

################################################################################
# MAIN
#
if __name__ == "__main__":

    # used only if the script is called from HAL/init
    # parses the josn that was created with the GUI
    if len(sys.argv) > 1:
        parse_json(sys.argv[1])

    ############################################################################
    # SETUP EXPERIMENT
    mx.initialize()
    sleep(5)
    if mx.send(mx.Core().enable_stimulation_power(True)) != "Ok":
        raise RuntimeError("The system didn't initialize correctly.")
    sleep(mx.Timing.waitInit)

    print("Initializing wells...")

    # sets up recording and stimulation electrodes for each well
    for well in wells:

        print(f"Setting up well {well}...")

        # activate the current well
        mx.activate([well])
        mx.set_primary_well(well)

        # get config file and recording electrode numbers
        # config_file = configs[well]
        # recording_electrodes = get_config_electrodes(config_file)
        recording_electrodes = configs[well] 

        # grab the stimulation electrodes
        stim_elecs = stimulation_electrodes[well]
        print(f"Stimulation electrodes: {stim_elecs}")

        array = mx.chip.Array("stimulation")

        # set recording and stimulation electrodes
        #
        # Note: stimulation electrodes must also be recording electrodes
        #array.reset()
        array.clear_selected_electrodes( )
        array.select_electrodes(recording_electrodes)
        array.select_stimulation_electrodes(stim_elecs)
        array.route()

        # connect stimulation units
        stimulation_units = hal.connect_stim_units_to_stim_electrodes(
            stim_elecs, array
        )

        # download data to the well
        array.download([well])

        # power up stimulation units
        for stim_unit in stimulation_units:
            mx.send(
                mx.StimulationUnit(stim_unit)
                .power_up(True)
                .connect(True)
                .set_voltage_mode()
                .dac_source(0)
            )

    mx.activate(wells)

    print("Offsetting...")
    sleep(mx.Timing.waitAfterDownload)
    mx.offset()
    sleep(15)

    mx.clear_events()

    print("Making stimulations...")

    #<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

    amp_list = [10, 100, 150, 200, 300, 500, 700]
    freq_list = [0.5, 1, 5, 10, 50, 100]

    stim_array = [None]*6   # A list for 6 wells
    for wid in range(6):
        stim_array[wid] = [None]*len(amp_list)
        for i, stim_amp in enumerate(amp_list):
            stim_array[wid][i] = Stimulation.from_frequency(str(freq_list[wid]) + "_Hz", 0,
                                    frequency=freq_list[wid],
                                    duration=max(10/freq_list[wid], 2),
                                    amplitude = stim_amp,
                                    phase = 200,
                                    well=0
                                    )
            
    stim_seq_array = [None]*6   # A list for 6 wells
    for wid in range(6):
        stim_seq_array[wid] = [None]*len(amp_list)
        for i, stim_amp in enumerate(amp_list):
            stim_seq_array[wid][i] = stim_array[wid][i].build_sequence()


    ############################################################################
    # RUN EXPERIMENT

    s = mx.Saving()
    s.open_directory(recording_dir)
    s.start_file(file_name)

    for well in wells:
        s.group_define(well, "all_channels", list(range(1024)))

    s.start_recording(wells)

    
    #<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
    # @edit
    #
    # Send stimulations and configure experiment timings here

    print("Starting recording...")
    sleep(5)

    for wid in range(6):
        for i, stim_amp in enumerate(amp_list):
            mx.set_primary_well(0)
            mx.activate([0])
            print("Sending stimulations to well " + str(0) + " at " + str(freq_list[wid]) + "Hz")
            stim_seq_array[wid][i].send()
            sleep(stim_array[wid][i].duration + 0.5)

    print("Sleeping for a hot 10 seconds b/c holy moly...")
    sleep(10)

    # end of recording
    #>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    
    # stop recording
    s.stop_recording()
    sleep(mx.Timing.waitAfterRecording)
    s.stop_file()
    s.group_delete_all()
    
