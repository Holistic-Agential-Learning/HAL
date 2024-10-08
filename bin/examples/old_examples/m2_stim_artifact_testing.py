#!/usr/bin/env python

# m2_stim_artifact_testing
#
# This is an open loop testing script that should stimulate all 6 wells at various frequencies, 
# at varying amplitudes on a blank chip, to get a baseline level of stimulation artifact. 
# Chips should not have water in them, but CMM or DPBS. 
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

# TODO
#
# parent directory of experiment data
parent_dir = "/home/mxwbio/Desktop/HAL/data/stimulation_artifact/"

# TODO
#
# name of the experiment
experiment_name = "6_well_test" 

# TODO
chip_id = "M012345"

# TODO
#
# wells to record from (just use 0 if using the MaxOne)
# Any missing wells here will cause the program to ignore their respective 
# recording and stimulatoin electrodes
wells = [0, 1, 2, 3, 4, 5] 

# TODO 
#
# description of the experiment, stored in the h5 file under "description"
description = "stimulates all 6 wells at various frequencies, at varying amplitudes on a blank chip, to get a baseline level of stimulation artifact."


# TODO
#
# Modify this to contain the FULL PATH of configs for each well. Just use the 
# first element of the list if using the MaxOne
with open("/home/mxwbio/Desktop/HAL/Ephaptic/configs/caspfiguration_center.txt", 'r') as f:
    center_rec_elecs = [int(row[0]) for row in csv.reader(f, delimiter='\t')]


# TODO
#
# recording electrodes for each well as either a list of integers or a full 
# path to a MaxWell electrode configuration file
recording_electrodes = [
    center_rec_elecs, # well 0 config
    center_rec_elecs, # well 1 config
    center_rec_elecs, # well 2 config
    center_rec_elecs, # well 3 config
    center_rec_elecs, # well 4 config
    center_rec_elecs, # well 5 config
]


# TODO
#
# Modify this to contain the stimulation electrodes for each well. Note that 
# these are electrode numbers (0-26399). Just use the first element of the list 
# if using the MaxOne.
#
# Important note: stimulation electrodes MUST come from the set of recording 
# electrodes defined above. 
stimulation_electrodes = [
    [13310], # well 1 stimulation electrodes
    [13310], # well 2 stimulation electrodes
    [13310], # well 3 stimulation electrodes 
    [13310], # well 4 stimulation electrodes
    [13310], # well 5 stimulation electrodes
    [13310]  # well 6 stimulation electrodes
]

################################################################################
# MAIN
#
if __name__ == "__main__":

    ############################################################################
    # SETUP EXPERIMENT

    # creates folders for experiment data
    trial_path = hal.make_trial_folders_raw(parent_dir, experiment_name, chip_id, wells) #TODO
    
    mx.initialize()
    sleep(5)
    if mx.send(mx.Core().enable_stimulation_power(True)) != "Ok":
        raise RuntimeError("The system didn't initialize correctly.")
    sleep(mx.Timing.waitInit)

    print("Initializing wells...")

    # sets up recording and stimulation electrodes for each well
    for well in wells:

        print(f"Setting up well {well}...")


        # get config file and recording electrode numbers
        rec_elecs = recording_electrodes[well] 

        # grab the stimulation electrodes
        stim_elecs = stimulation_electrodes[well]
        # print(f"Stimulation electrodes: {stim_elecs}")

        # upload recording electrodes and power up stimulation units
        array = hal.init_well(well, rec_elecs, stim_elecs)

        # TODO optional: save configuration for each well for future reference
        # array.save_config(f"{trial_path}/{experiment_name}_well{well}.cfg")

    mx.activate(wells)

    # TODO come back to this after testing...offset happens for each well in 
    # hal.init_well
    # why do we need to sleep so much here? can we take this out?
    # print("Offsetting...")
    # sleep(mx.Timing.waitAfterDownload)
    # mx.offset()
    # sleep(15)


    print("Making stimulations...")

    #<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

    amp_list = [10, 100, 150, 200, 300, 500, 700]
    freq_list = [0.5, 1, 5, 10, 50, 100]

    # ask Wes 

    stim_array = []  # list of stimulations with varying amplitudes and frequencies

    for freq in freq_list:
        amp_stims = []
        for amp in amp_list:
            amp_stims.append(Stimulation.from_frequency(f"{freq}_Hz-{amp}_mV", 
                                    dac_source = 0,
                                    frequency = freq,
                                    duration = max(10 / freq, 2),
                                    amplitude = amp,
                                    phase = 200))
        stim_array.append(amp_stims)
            
    stim_seq_array = []   # A list for 6 wells
    for freq_idx in len(freq_list):
        amp_seqs = []
        for amp_idx in len(amp_list):
            amp_seqs.append(stim_array[freq_idx][amp_idx].build_sequence())
        stim_seq_array.append(amp_seqs)


    ############################################################################
    # RUN EXPERIMENT

    s = mx.Saving()
    s.open_directory(trial_path)
    s.start_file(experiment_name)

    for well in wells:
        s.group_define(well, f"all_channels{well}", list(range(1024)))

    s.start_recording(wells)

    
    #<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
    # TODO
    #
    # Send stimulations and configure experiment timings here

    print("Starting recording...")
    sleep(5)
    for well in wells:
        mx.set_primary_well(well)
        mx.activate([well])
        for freq_idx in len(freq_list):
            for amp_idx in len(amp_list):
                print(f"Sending stimulation to well {well} at {freq_list[freq_idx]} Hz and {amp_list[amp_idx]} mV")
                stim_seq_array[freq_idx][amp_idx].send()
                sleep(stim_array[freq_idx][amp_idx].duration + 0.5)
            print("Pausing for 10 seconds before next well...")
            sleep(10)

    # end of recording
    #>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    
    # stop recording
    s.stop_recording()
    sleep(mx.Timing.waitAfterRecording)
    s.stop_file()
    s.group_delete_all()
    
