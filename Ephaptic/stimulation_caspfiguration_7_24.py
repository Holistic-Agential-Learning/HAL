#!/usr/bin/env python

# m2_stimulation_assay_example
#
# This code runs a 50 / 100 Hz stimulation of one central electrode for 10 minutes and measures from a 
# custom-made set of electrodes around it with a power-law resolution decrease around the stimulation site.
#  
#
# Long lines of '#' characters divide sections of code
#
# Run with:
#
#       ./stimulation_caspfiguration.py
#
# Written by Daniel Rebbin, adapted from Trevor Sullivan
# July 23, 2024

import maxlab as mx

from typing import List
from time import sleep
from h5py import File

import json
import sys
import csv
import numpy as np

################################################################################
# GLOBAL VARIABLES

# @edit
#
# file name of the h5 file where the recording data is stored
file_name = "ephaptic_stimulation_caspfiguration" 


# @edit
#
# directory to store recording file
recording_dir = "/home/mxwbio/Desktop/HAL/data/ephaptic"


# wells to record from
wells = range(6) 


# @edit
#
# Modify this to contain the FULL PATH of configs for each well. 
import_configs_l = with open("/home/mxwbio/Desktop/HAL/Ephaptic/configs/caspfiguration_left_M07458.txt", 'r') as f:
    first_row = [row[0] for row in csv.reader(f, delimiter='\t')]
    print(first_row)
    

# record_electrods = [

# ]
# configs = [
#     ".../caspfiguration_left.txt", # well 0 config
#     ".../caspfiguration_right.txt", # well 1 config
#     ".../caspfiguration_left.txt", # well 2 config
#     ".../caspfiguration_right.txt", # well 3 config
#     ".../caspfiguration_left.txt", # well 4 config
#     ".../caspfiguration_right.txt" # well 5 config
# ]


# # Define stimulation electrodes 
# stimulation_electrodes = [
#     [], # well 0 stimulation electrode: none
#     [], # well 1 stimulation electrode: none
#     [13260], # well 2 stimulation electrode: left center
#     [13360], # well 3 stimulation electrode: right center
#     [13260], # well 4 stimulation electrode: left center
#     [13360]  # well 5 stimulation electrode: right center
# ]


# ################################################################################
# # HELPER FUNCTIONS

# # function for connecting stimulation units to stimulation electrodes
# def connect_stim_units_to_stim_electrodes(
#     stim_electrodes: List[int], array: mx.Array
# ) -> List[int]:
#     stim_units: List[int] = []
#     for stim_el in stim_electrodes:
#         array.connect_electrode_to_stimulation(stim_el)
#         stim = array.query_stimulation_at_electrode(stim_el)
#         if len(stim) == 0:
#             raise RuntimeError(
#                 f"No stimulation channel can connect to electrode: \
#                     {str(stim_el)}"
#             )
#         stim_unit_int = int(stim)
#         if stim_unit_int in stim_units:
#             raise RuntimeError(
#                 f"Two electrodes connected to the same stim unit. This is not \
#                   allowed. Please Select a neighboring electrode of {stim_el}!"
#             )
#         else:
#             stim_units.append(stim_unit_int)
#     return stim_units

# # function for reading in electrode numbers from a .txt file
# def get_config_electrodes(file_path):
#     with open(file_path, 'r') as file:
#         electrode_nums = [int(line.strip()) for line in file.readlines()]
#     return electrode_nums

# # parses json that was created with the GUI
# def parse_json(json_name):
#     global file_name, recording_dir, wells, configs
#     f = open(json_name, "r")
#     params = json.load(f)
#     f.close()

#     wells = params['WELLS']

#     file_name = params['NAME']
#     recording_dir = params['FOLDER']

#     for well in wells:
#         configs[well] = params['CONFIGS'][str(well)]['PATH']

# ################################################################################
# # MAIN
# #
# if __name__ == "__main__":

#     # used only if the script is called from HAL/init
#     # parses the josn that was created with the GUI
#     if len(sys.argv) > 1:
#         parse_json(sys.argv[1])

#     ############################################################################
#     # SETUP EXPERIMENT
#     mx.initialize()
#     sleep(5)
#     if mx.send(mx.Core().enable_stimulation_power(True)) != "Ok":
#         raise RuntimeError("The system didn't initialize correctly.")
#     sleep(mx.Timing.waitInit)

#     print("Initializing wells...")

#     # sets up recording and stimulation electrodes for each well
#     for well in wells:

#         print(f"Setting up well {well}...")

#         # activate the current well
#         mx.activate([well])
#         mx.set_primary_well(well)

#         # get config file and recording electrode numbers
#         config_file = configs[well]
#         recording_electrodes = get_config_electrodes(config_file)

#         # grab the stimulation electrodes
#         stim_elecs = stimulation_electrodes[well]

#         array = mx.chip.Array("stimulation")

#         # set recording and stimulation electrodes
#         #
#         # Note: stimulation electrodes must also be recording electrodes
#         array.select_electrodes(recording_electrodes)
#         array.select_stimulation_electrodes(stim_elecs)
#         array.route()

#         # connect stimulation units
#         stimulation_units = connect_stim_units_to_stim_electrodes(
#             stim_elecs, array
#         )

#         # power up stimulation units
#         for stim_unit in stimulation_units:
#             mx.send(
#                 mx.StimulationUnit(stim_unit)
#                 .power_up(True)
#                 .connect(True)
#                 .set_voltage_mode()
#                 .dac_source(0)
#             )

#         # download data to the well
#         array.download([well])

#     mx.activate(wells)

#     print("Offsetting...")
#     sleep(mx.Timing.waitAfterDownload)
#     mx.offset()
#     sleep(15)

#     mx.clear_events()

#     print("Making stimulations...")

#     #<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

#     # Define stimulation parameters
#     number_pulses_per_train = 20
#     amplitude = 34  # to get roughly 100 mV
#     #phase = 100
#     inter_pulse_interval = 400 # to get a 50 Hz rhythm
#     number_pulse_trains = 750 # 10 minutes of stimulation in total
    

#     event_id = 1 # always contains a unique event ID if updated after each event
#     pulse_num = 0

#     fifty_Hz_sequence = mx.Sequence("50_Hz_stimulation")

#     # add event to indicate the start of the stimulation
#     fifty_Hz_sequence.append(mx.Event(wells[2], 1, event_id, 
#                                 "before_stim 50hz"))
#     event_id += 1 # make sure that the event ID is always unique
    

#     # send trains
#     for _ in range(number_pulse_trains):
#         for _ in range(number_pulses_per_train):
#             pulse_num += 1
#             fifty_Hz_sequence.append(mx.Event(wells[2], 1, event_id, 
#                                     f"pulse_start {pulse_num} freq 50hz"))
#             event_id += 1
#             # amplitude
#             fifty_Hz_sequence.append(mx.DAC(0, 512 - amplitude))

#             # phase
#             fifty_Hz_sequence.append(mx.DelaySamples(2)) # 100 us
#             fifty_Hz_sequence.append(mx.DAC(0, 512 + amplitude))
#             fifty_Hz_sequence.append(mx.DelaySamples(2))
#             fifty_Hz_sequence.append(mx.DAC(0, 512))

#             fifty_Hz_sequence.append(mx.Event(wells[2], 1, event_id, 
#                                     f"pulse_end {pulse_num} freq 50hz"))
#             event_id += 1

#             # inter pulse interval
#             fifty_Hz_sequence.append(mx.DelaySamples(inter_pulse_interval-4))
        
#         # Delay as to have stimulation initations 800ms apart 
#         fifty_Hz_sequence.append(mx.DelaySamples(8000))

    
#     # add event to indicate the end of the stimulation
#     fifty_Hz_sequence.append(mx.Event(wells[2], 1, event_id, 
#                                 "after_stim 50hz"))

#     #>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

#     #<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

#     # Define stimulation parameters
#     number_pulses_per_train = 20
#     amplitude = 34  # to get roughly 100 mV
#     phase = 100
#     inter_pulse_interval = 200 # to get a 100 Hz rhythm
#     number_pulse_trains = 750 # 10 minutes of stimulation in total
    
#     #NOTE: Need to check if using the same event ids with different wells works.
#     event_id = 1 # always contains a unique event ID if updated after each event
#     pulse_num = 0

#     hundred_Hz_sequence = mx.Sequence("100_Hz_stimulation")

#     # add event to indicate the start of the stimulation
#     hundred_Hz_sequence.append(mx.Event(wells[4], 1, event_id, 
#                                 "before_stim 100hz"))
#     event_id += 1 # make sure that the event ID is always unique

#     # sendtrains
#     for _ in range(number_pulse_trains):
#         for _ in range(number_pulses_per_train):
#             pulse_num += 1
#             hundred_Hz_sequence.append(mx.Event(wells[4], 1, event_id, 
#                                     f"pulse_start {pulse_num} freq 100hz"))
#             event_id += 1
#             # amplitude
#             hundred_Hz_sequence.append(mx.DAC(0, 512 - amplitude))

#             # phase
#             hundred_Hz_sequence.append(mx.DelaySamples(2))
#             hundred_Hz_sequence.append(mx.DAC(0, 512 + amplitude))
#             hundred_Hz_sequence.append(mx.DelaySamples(2))
#             hundred_Hz_sequence.append(mx.DAC(0, 512))

#             hundred_Hz_sequence.append(mx.Event(wells[4], 1, event_id, 
#                         f"pulse_end {pulse_num} freq 100hz"))
#             event_id += 1

#             # inter pulse interval
#             hundred_Hz_sequence.append(mx.DelaySamples(inter_pulse_interval-4))
        
#         # Delay as to have stimulation initations 800ms apart 
#         hundred_Hz_sequence.append(mx.DelaySamples(12000))

    
#     # add event to indicate the end of the stimulation
#     hundred_Hz_sequence.append(mx.Event(wells[4], 1, event_id, 
#                                 "after_stim 100hz"))

#     #>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    
#     ############################################################################
#     # RUN EXPERIMENT

#     s = mx.Saving()
#     s.open_directory(recording_dir)
#     s.start_file(file_name)

#     for well in wells:

record_electrods = [

]
configs = [
    ".../caspfiguration_left.txt", # well 0 config
    ".../caspfiguration_right.txt", # well 1 config
    ".../caspfiguration_left.txt", # well 2 config
    ".../caspfiguration_right.txt", # well 3 config
    ".../caspfiguration_left.txt", # well 4 config
    ".../caspfiguration_right.txt" # well 5 config
]


# Define stimulation electrodes 
stimulation_electrodes = [
    [], # well 0 stimulation electrode: none
    [], # well 1 stimulation electrode: none
    [13260], # well 2 stimulation electrode: left center
    [13360], # well 3 stimulation electrode: right center
    [13260], # well 4 stimulation electrode: left center
    [13360]  # well 5 stimulation electrode: right center
]


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

# function for reading in electrode numbers from a .txt file
def get_config_electrodes(file_path):
    with open(file_path, 'r') as file:
        electrode_nums = [int(line.strip()) for line in file.readlines()]
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
        config_file = configs[well]
        recording_electrodes = get_config_electrodes(config_file)

        # grab the stimulation electrodes
        stim_elecs = stimulation_electrodes[well]

        array = mx.chip.Array("stimulation")

        # set recording and stimulation electrodes
        #
        # Note: stimulation electrodes must also be recording electrodes
        array.select_electrodes(recording_electrodes)
        array.select_stimulation_electrodes(stim_elecs)
        array.route()

        # connect stimulation units
        stimulation_units = connect_stim_units_to_stim_electrodes(
            stim_elecs, array
        )

        # power up stimulation units
        for stim_unit in stimulation_units:
            mx.send(
                mx.StimulationUnit(stim_unit)
                .power_up(True)
                .connect(True)
                .set_voltage_mode()
                .dac_source(0)
            )

        # download data to the well
        array.download([well])

    mx.activate(wells)

    print("Offsetting...")
    sleep(mx.Timing.waitAfterDownload)
    mx.offset()
    sleep(15)

    mx.clear_events()

    print("Making stimulations...")

    #<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

    # Define stimulation parameters
    number_pulses_per_train = 20
    amplitude = 34  # to get roughly 100 mV
    #phase = 100
    inter_pulse_interval = 400 # to get a 50 Hz rhythm
    number_pulse_trains = 750 # 10 minutes of stimulation in total
    

    event_id = 1 # always contains a unique event ID if updated after each event
    pulse_num = 0

    fifty_Hz_sequence = mx.Sequence("50_Hz_stimulation")

    # add event to indicate the start of the stimulation
    fifty_Hz_sequence.append(mx.Event(wells[2], 1, event_id, 
                                "before_stim 50hz"))
    event_id += 1 # make sure that the event ID is always unique
    

    # send trains
    for _ in range(number_pulse_trains):
        for _ in range(number_pulses_per_train):
            pulse_num += 1
            fifty_Hz_sequence.append(mx.Event(wells[2], 1, event_id, 
                                    f"pulse_start {pulse_num} freq 50hz"))
            event_id += 1
            # amplitude
            fifty_Hz_sequence.append(mx.DAC(0, 512 - amplitude))

            # phase
            fifty_Hz_sequence.append(mx.DelaySamples(2)) # 100 us
            fifty_Hz_sequence.append(mx.DAC(0, 512 + amplitude))
            fifty_Hz_sequence.append(mx.DelaySamples(2))
            fifty_Hz_sequence.append(mx.DAC(0, 512))

            fifty_Hz_sequence.append(mx.Event(wells[2], 1, event_id, 
                                    f"pulse_end {pulse_num} freq 50hz"))
            event_id += 1

            # inter pulse interval
            fifty_Hz_sequence.append(mx.DelaySamples(inter_pulse_interval-4))
        
        # Delay as to have stimulation initations 800ms apart 
        fifty_Hz_sequence.append(mx.DelaySamples(8000))

    
    # add event to indicate the end of the stimulation
    fifty_Hz_sequence.append(mx.Event(wells[2], 1, event_id, 
                                "after_stim 50hz"))

    #>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

    #<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

    # Define stimulation parameters
    number_pulses_per_train = 20
    amplitude = 34  # to get roughly 100 mV
    phase = 100
    inter_pulse_interval = 200 # to get a 100 Hz rhythm
    number_pulse_trains = 750 # 10 minutes of stimulation in total
    
    #NOTE: Need to check if using the same event ids with different wells works.
    event_id = 1 # always contains a unique event ID if updated after each event
    pulse_num = 0

    hundred_Hz_sequence = mx.Sequence("100_Hz_stimulation")

    # add event to indicate the start of the stimulation
    hundred_Hz_sequence.append(mx.Event(wells[4], 1, event_id, 
                                "before_stim 100hz"))
    event_id += 1 # make sure that the event ID is always unique

    # sendtrains
    for _ in range(number_pulse_trains):
        for _ in range(number_pulses_per_train):
            pulse_num += 1
            hundred_Hz_sequence.append(mx.Event(wells[4], 1, event_id, 
                                    f"pulse_start {pulse_num} freq 100hz"))
            event_id += 1
            # amplitude
            hundred_Hz_sequence.append(mx.DAC(0, 512 - amplitude))

            # phase
            hundred_Hz_sequence.append(mx.DelaySamples(2))
            hundred_Hz_sequence.append(mx.DAC(0, 512 + amplitude))
            hundred_Hz_sequence.append(mx.DelaySamples(2))
            hundred_Hz_sequence.append(mx.DAC(0, 512))

            hundred_Hz_sequence.append(mx.Event(wells[4], 1, event_id, 
                        f"pulse_end {pulse_num} freq 100hz"))
            event_id += 1

            # inter pulse interval
            hundred_Hz_sequence.append(mx.DelaySamples(inter_pulse_interval-4))
        
        # Delay as to have stimulation initations 800ms apart 
        hundred_Hz_sequence.append(mx.DelaySamples(12000))

    
    # add event to indicate the end of the stimulation
    hundred_Hz_sequence.append(mx.Event(wells[4], 1, event_id, 
                                "after_stim 100hz"))

    #>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    
    ############################################################################
    # RUN EXPERIMENT

    s = mx.Saving()
    s.open_directory(recording_dir)
    s.start_file(file_name)

    for well in wells:
        s.group_define(well, "all_channels", list(range(1024)))

    s.start_recording(wells)

    #<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
    # Send stimulations and configure experiment
    
    # Recording half an hour from each well
    # 10 minutes pre- and post-stimulation time recorded
    pre_stimulation_time = 600
    post_stimulation_time = 600

    print("Start recording...")

    # record reference from wells 0 and 1
    for well in range(2):
        mx.set_primary_well(well)
        mx.activate([well])
        sleep(pre_stimulation_time)
        print(f"Sending sham stimulation to {well}...")
        sleep(600) # ten minutes where stimulation happens in the other condition
        sleep(post_stimulation_time)

    # stimulate wells 2 and 3 with 50 Hz
    for well in range(2, 4):
        mx.set_primary_well(well)
        mx.activate([well])
        sleep(pre_stimulation_time)
        print(f"Sending 50 Hz stimulation to well {well}...")
        fifty_Hz_sequence.send()
        sleep(post_stimulation_time)

    # stimulate wells 4 and 5 with 100 Hz
    for well in range(4, 6):
        mx.set_primary_well(well)
        mx.activate([well])
        sleep(pre_stimulation_time)
        print(f"Sending 100 Hz stimulation to well {well}...")
        hundred_Hz_sequence.send()
        sleep(post_stimulation_time)

    print("Stop recording...")

    # end of recording
    #>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    
    # stop recording
    s.stop_recording()
    sleep(mx.Timing.waitAfterRecording)
    s.stop_file()
    s.group_delete_all()
    

#     # end of recording
#     #>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    
#     # stop recording
#     s.stop_recording()
#     sleep(mx.Timing.waitAfterRecording)
#     s.stop_file()
#     s.group_delete_all()
    
