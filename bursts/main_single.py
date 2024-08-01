#!/usr/bin/env python

import maxlab as mx
from typing import List
from time import sleep
from h5py import File
import os
import sys
sys.path.append("..")
import bin.lib.py_src.hal as hal
from bin.lib.py_src.stimulation import Stimulation

main_dict = {"FOLDER": "/home/mxwbio/Desktop/HAL/data/burst_control/M07470", #TODO: change the chipID
 "NAME": "burst_control",
 "WELLS": [4]} #TODO: change the well

file_name = main_dict["NAME"]
trial_path = hal.make_trial_folders(main_dict)
wells = main_dict["WELLS"]
recording_dir = f"{trial_path}/well{wells[0]}"

configs = ["/home/mxwbio/configs/240731/14h55m46s.cfg"] #TODO: change this coonfig
stim_electrode_single = [ 3317,21799,4385,20653] #TODO: change these electrodes


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

if __name__ == "__main__":

    mx.initialize()
    sleep(5)
    if mx.send(mx.Core().enable_stimulation_power(True)) != "Ok":
        raise RuntimeError("The system didn't initialize correctly.")
    sleep(mx.Timing.waitInit)
    print("Initializing wells...")

    for well in wells:
        print(f"Setting up well {well}...")
        mx.activate([well])
        mx.set_primary_well(well)
        config_file = configs[0]
        recording_electrodes = get_config_electrodes(config_file)
        stim_elecs_a = stim_electrode_single
        array = mx.chip.Array("stimulation")
        array.select_electrodes(recording_electrodes)
        array.select_stimulation_electrodes(stim_elecs_a)
        array.route()
        stimulation_units = connect_stim_units_to_stim_electrodes(
            stim_elecs_a, array
        )
        for stim_unit in stimulation_units:
            mx.send(
                mx.StimulationUnit(stim_unit)
                .power_up(True)
                .connect(True)
                .set_voltage_mode()
                .dac_source(0)
            )
        array.download([well])

    mx.activate(wells)
    print("Offsetting...")
    sleep(mx.Timing.waitAfterDownload)
    mx.offset()
    sleep(15)
    mx.clear_events()
    print("Making stimulations...")

    #single high
    #10 stims/sec
    stim_single_high = Stimulation(token="stim_single_high", dac_source=0, amplitude=600, phase=400, pulses_per_train=1, num_trains=18_000, pulse_interval=0,  pulse_train_interval=0.0992, well=wells[0])
    stim_single_high_seq = stim_single_high.build_sequence()
    print(stim_single_high.get_duration())
    #single low
    #1 stim/10 sec
    stim_single_low = Stimulation(token = "stim_single_low", dac_source = 0,  amplitude=600, phase=400, pulses_per_train=1, num_trains=180, pulse_interval=0,  pulse_train_interval=9.9992, well=wells[0])
    
    stim_single_low_seq = stim_single_low.build_sequence()
    print(stim_single_low.get_duration())

    # stim_single_low = Stimulation.combine_stimuli(timing_stimulation, stim_single_low_stims, "stim_single_low")
    # stim_single_low_seq = stim_single_low.build_sequence()



    s = mx.Saving()
    s.open_directory(recording_dir)
    s.start_file(file_name)

    for well in wells:
        s.group_define(well, "all_channels", list(range(1024))) #TODO: is this correct?

    s.start_recording(wells)

    print("Starting recording...")
    sleep(5)

    print("Sending first stimulation...")
    #stim_single_low_seq.send() # send stimulation 
    stim_single_low_seq.send()
    sleep(1800) # wait for 30 mins

    print("Sending second stimulation...")
    stim_single_high_seq.send()
    sleep(1800)

    #now for none
    print("sending nothing :P")
    sleep(1800)
    
    # stop recording
    s.stop_recording()
    sleep(mx.Timing.waitAfterRecording)
    s.stop_file()
    s.group_delete_all()
