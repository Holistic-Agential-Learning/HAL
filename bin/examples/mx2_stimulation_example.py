# mx2_stimulation_example
#
# This is a basic file for running custom simulation on the MaxOne/Two. 
# Intruction comments for creating your own experiments are dispersed 
# throughout the file and are tagged with @edit
#
# Written by Trevor M. Sullivan
# July 2, 2024

import maxlab as mx
import matplotlib.pyplot as plt

from typing import List
from time import sleep
from h5py import File
from pathlib import Path

################################################################################
# GLOBAL VARIABLES

# @edit
# file name for recording (h5) file
file_name = "stim" 


# @edit
# directory to store recording file
recording_dir = str("/home/mxwbio/Desktop/HAL/data/triple_stim")


# @edit
# wells to record from (just use 0 if using the MaxOne)
wells = [0, 1, 2] 


# @edit
#
# Modify this to contain the FULL PATH of configs for each well. Just use the 
# first element of the list if using the MaxOne
configs = [
    "/home/mxwbio/Desktop/HAL/test_config_2.cfg", # well 0 config
    "", # well 1 config
    "", # ...
    "",
    "",
    ""
]


# @edit
#
# Modify this to contain the stimulation electrodes for each well. Note that 
# these are electrode numbers (0-26399). Just use the first element of the list 
# if using the MaxOne
stimulation_electrodes = [
    [1000, 2000, 3000], # well 0 stimulation electrodes
    [], # well 1 stimulation electrodes
    [], # ... 
    [],
    [],
    []
]


# Parameters of the Stimulation
amplitude_A = 10  # bits
amplitude_B = 50  # bits

phase = 100  # samples -> MX1: 100/20000 = 5 ms
inter_pulse_interval = 10000  # samples -> MX1: 1000/20000 = 0.5 s


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
                f"No stimulation channel can connect to electrode: {str(stim_el)}"
            )
        stim_unit_int = int(stim)
        if stim_unit_int in stim_units:
            raise RuntimeError(
                f"Two electrodes connected to the same stim unit. This is not allowed. Please Select a neighboring electrode of {stim_el}!"
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
    
    return electrode_nums

################################################################################
# MAIN
#
if __name__ == "__main__":
    # SETUP
    mx.initialize()
    sleep(5)
    if mx.send(mx.Core().enable_stimulation_power(True)) != "Ok":
        raise RuntimeError("The system didn't initialize correctly.")
    sleep(mx.Timing.waitInit)

    # sets up recording and stimulation electrodes for each well
    for well in wells:

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
        #       Note: stimulation electrodes must also be recording electrodes, 
        #             so they are automatically added here
        array.select_electrodes(stim_elecs + recording_electrodes)
        array.select_stimulation_electrodes(stimulation_electrodes)
        array.route()

        # connect stimulation units
        stimulation_units = connect_stim_units_to_stim_electrodes(
            stim_elecs, array
        )

        # get channels for stimulation electrodes?
        # config = array.get_config()
        # stimulation_channels = config.get_channels_for_electrodes(stim_elecs)
        # stimulation_channels.sort()

        mx.send(
            mx.StimulationUnit(stimulation_units[0])
            .power_up(True)
            .connect(True)
            .set_voltage_mode()
            .dac_source(0)
        )

        # download data to the well
        array.download([well])

    sleep(mx.Timing.waitAfterDownload)
    mx.offset()
    sleep(15)

    mx.clear_events()

    # START EXPERIMENT
    s = mx.Saving()
    s.open_directory(recording_dir)
    s.start_file(file_name)

    for well in wells:
        s.group_define(well, "all_channels", list(range(1024)))

    # @edit
    #
    # The next chunk of code defines a stimulation sequence.
    # 
    # Notes:
    #   - The string in mx.Sequence() must be a unique identifier for each 
    #     sequence
    sequence1 = mx.Sequence("1")
    for _ in range(3):
        sequence1.append(mx.DAC(0, 512 + amplitude_A))
        sequence1.append(mx.DelaySamples(phase))
        sequence1.append(mx.DAC(0, 512))
        sequence1.append(mx.DelaySamples(inter_pulse_interval))

    sequence2 = mx.Sequence("2")
    for _ in range(5):
        sequence2.append(mx.DAC(1, 512 + amplitude_B))
        sequence2.append(mx.DelaySamples(phase))
        sequence2.append(mx.DAC(1, 512))
        sequence2.append(mx.DelaySamples(inter_pulse_interval))

    s.start_recording(wells)

    print("Start recording")
    sleep(5)  # Pre-stimulation time

    print("Sending first stimulation...")
    sequence1.send() # send stimulation 
    sleep(5) # wait for 5 seconds

    print("Sending second stimulation...")
    sequence1.send()
    sleep(5)

    print("Sending third stimulation...")
    sequence1.send()
    sleep(5)

    s.stop_recording()
    sleep(mx.Timing.waitAfterRecording)
    s.stop_file()
    s.group_delete_all()

    # del sequence1
    # del sequence2

    # print(stimulation_channels)

    # VERIFY RESULTS
    # file = File(f"{recording_dir}/{file_name}.raw.h5")
    # raw_trace_A = file["wells/well000/rec0000/groups/all_channels/raw"][
    #     stimulation_channels[0], :
    # ].T
    # raw_trace_B = file["wells/well001/rec0000/groups/all_channels/raw"][
    #     stimulation_channels[1], :
    # ].T

    # plt.plot(raw_trace_A)
    # plt.plot(raw_trace_B)
    # plt.show()
