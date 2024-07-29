#!/usr/bin/env python

# m2_stimulation_assay_example
#
# This is a basic example for running custom stimulations on the MaxOne/Two.
#  
# Intruction comments for creating your own experiments are dispersed 
# throughout the file and are tagged with '@edit'. Large chunks of code to edit
# begin with a line of '<' characters and end with a line of '>' characters.
#
# Long lines of '#' characters divide sections of code
#
# Run with:
#
#       ./m2_stimulation_assay_example.py
#
# Written by Trevor M. Sullivan
# July 2, 2024

import maxlab as mx

from typing import List
from time import sleep
from h5py import File

import json
import sys

################################################################################
# GLOBAL VARIABLES

# @edit
#
# file name of the h5 file where the recording data is stored
file_name = "stimulation_example" 


# @edit
#
# directory to store recording file
recording_dir = "/home/mxwbio/Desktop/HAL/data/stimulation_assay_example"


# @edit
#
# wells to record from (just use 0 if using the MaxOne)
wells = [0] 


# @edit
#
# Modify this to contain the FULL PATH of configs for each well. Just use the 
# first element of the list if using the MaxOne
configs = [
    "/home/mxwbio/Desktop/HAL/test_config_2.cfg", # well 0 config
    "/home/mxwbio/Desktop/HAL/test_config_2.cfg", # well 1 config
    "", # ...
    "",
    "",
    ""
]


# @edit
#
# Modify this to contain the stimulation electrodes for each well. Note that 
# these are electrode numbers (0-26399). Just use the first element of the list 
# if using the MaxOne.
#
# Important note: stimulation electrodes MUST come from the set of recording 
# electrodes defined above. 
stimulation_electrodes = [
    [14915, 14551, 20550], # well 0 stimulation electrodes
    [20590], # well 1 stimulation electrodes
    [], # ... 
    [],
    [],
    []
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
        config_file = configs[well]
        recording_electrodes = get_config_electrodes(config_file)

        # grab the stimulation electrodes
        stim_elecs = stimulation_electrodes[well]
        print(f"Stimulation electrodes: {stim_elecs}")

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
    # @edit
    #
    # Define stimulation sequences here.
    # 
    # Notes:
    #   - The string in mx.Sequence() must be a unique identifier for each 
    #     sequence
    #   - An event can only correspond to one well--if you want it to be visible
    #     on all wells, then you have to make an event for each well
    #   - mx.Event arguments (in order):
    #       - well number
    #       - the integer 1 (this is the only way that it works)
    #       - unique unique positive integer used as an identifier for each 
    #         event (CANNOT be less than 1)
    #       - a string key-value pair, separated by a space (can be used to 
    #         describe the event)

    event_id = 1 # always contains a unique event ID if updated after each event

    example_sequence = mx.Sequence("example_stimulation")

    # add event to indicate the start of the stimulation
    example_sequence.append(mx.Event(wells[0], 1, event_id, 
                                "before example_stimulation"))
    event_id += 1 # make sure that the event ID is always unique

    # send 3 trains
    for _ in range(3):

        # amplitude
        example_sequence.append(mx.DAC(0, 512 + 10))

        # phase
        example_sequence.append(mx.DelaySamples(100))
        example_sequence.append(mx.DAC(0, 512))

        # inter pulse interval
        example_sequence.append(mx.DelaySamples(10000))
    
    # add event to indicate the end of the stimulation
    example_sequence.append(mx.Event(wells[0], 1, event_id, 
                                "after example_stimulation"))
    event_id += 1

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
    # @edit
    #
    # Send stimulations and configure experiment timings here

    print("Starting recording...")
    sleep(5)

    # this will stimulate all wells, since they are all activated
    print("Sending first stimulation...")
    example_sequence.send() # send stimulation 
    sleep(5) # wait for 5 seconds

    # switches which well is viewed in the MaxWell GUI 
    mx.set_primary_well(0)

    # use this to activate the wells that you want to stimulate...this will 
    # stimulate well 0
    mx.activate([0])
    print("Sending second stimulation...")
    example_sequence.send()
    sleep(5)

    mx.set_primary_well(1)

    # stimulate well 1
    mx.activate([1])
    print("Sending third stimulation...")
    example_sequence.send()
    sleep(5)

    # end of recording
    #>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    
    # stop recording
    s.stop_recording()
    sleep(mx.Timing.waitAfterRecording)
    s.stop_file()
    s.group_delete_all()
    
