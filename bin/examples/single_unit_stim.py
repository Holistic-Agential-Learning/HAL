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
file_name = "single_unit_stimulation_high_amp_low_phase" 


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

    # sets up recording and stimulation electrodes for each well
    for well in wells:

        print(f"Setting up well {well}...")

        # activate the current well
        mx.activate([well])
        mx.set_primary_well(well)

        # get config file and recording electrode numbers
        config_file = configs[well]
        recording_electrodes = get_config_electrodes(config_file)
        #recording_electrodes = configs[well] 

        # grab the stimulation electrodes
        stim_elecs = [stimulation_electrodes[well], stimulation_electrodes[well] + 1]
        print(f"Stimulation electrodes: {stim_elecs}")

        array = mx.chip.Array(f"stimulation{well}")

        # set recording and stimulation electrodes
        #
        # Note: stimulation electrodes must also be recording electrodes
        #array.reset()
        array.clear_selected_electrodes( )
        for row in range(stim_elecs[0] - 220 * 10, stim_elecs[0] + 220 * 11, 220):
            array.select_electrodes(range(row - 10, row + 11), 2)
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
        for i, stim_unit in enumerate(stimulation_units):
            mx.send(
                mx.StimulationUnit(stim_unit)
                .power_up(True)
                .connect(True)
                .set_voltage_mode()
                .dac_source(i)
            )

    mx.activate(wells)

    print("Offsetting...")
    sleep(mx.Timing.waitAfterDownload)
    mx.offset()
    sleep(15)

    mx.clear_events()

    print("Making stimulations...")

    #<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
    
    pulse_dict = dict()
    inverse_pulse_dict = dict()
    combined_dict = dict()

    pulse_seq_dict = dict()
    combined_seq_dict = dict()
    all_amps = [280, 320, 360]
    for amp in all_amps:
        pulse_dict[amp] = Stimulation(f"pulse_{amp}", 0, amp, 100, 1, 1, 1, 1)
        inverse_pulse_dict[amp] = Stimulation(f"inverse_pulse_{amp}", 1, -1 * amp, 100, 1, 1, 1, 1)

        combined_dict[amp] = Stimulation.combine_stimuli(pulse_dict[amp], inverse_pulse_dict[amp], f"combined_{amp}")

        pulse_seq_dict[amp] = pulse_dict[amp].build_sequence()
        combined_seq_dict[amp] = combined_dict[amp].build_sequence()

    ############################################################################
    # RUN EXPERIMENT

    s = mx.Saving()
    s.open_directory(recording_dir)
    s.start_file(file_name)

    for well in wells:
        s.group_define(well, f"all_channels_{well}", list(range(1024)))
        s.write_assay_property(f"stim_elecs_{well}", ", ".join(str(x) for x in [stimulation_electrodes[well], stimulation_electrodes[well] + 1]))

    s.start_recording(wells)

    
    #<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
    # @edit
    #
    # Send stimulations and configure experiment timings here

    print("Starting recording...")
    sleep(5)

    for amp in all_amps:
        print("individual pulses: amp = " + str(amp))
        for i in range(30):
            pulse_seq_dict[amp].send()
            sleep(4)
        print("negated pulses: amp = " + str(amp))
        for i in range(30):
            combined_seq_dict[amp].send()
            sleep(4)

    # end of recording
    #>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    
    # stop recording
    s.stop_recording()
    sleep(mx.Timing.waitAfterRecording)
    s.stop_file()
    s.group_delete_all()
    
