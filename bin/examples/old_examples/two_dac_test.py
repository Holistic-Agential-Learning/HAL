#!/bin/python3
import time
import random
import maxlab
import maxlab.system
import maxlab.chip
import maxlab.util


def append_stimulation_pulse(well, seq, id, dac, amplitude, delay):
    seq.append(maxlab.Event(well, 1, id, f"amplitude {amplitude} delay {delay}"))
    seq.append( maxlab.chip.DAC(dac, 512-amplitude) )
    seq.append( maxlab.system.DelaySamples(delay) )
    seq.append( maxlab.chip.DAC(dac, 512+amplitude) )
    seq.append( maxlab.system.DelaySamples(delay) )
    seq.append( maxlab.chip.DAC(dac, 512) )
    return seq

def append_conjoin_stimulation_pulse(well, seq, id, dac1, dac2, amplitude1, delay1, amplitude2, delay2):
    seq.append(maxlab.Event(well, 1, id, f"amplitude1 {amplitude1} delay1 {delay1} amplitude2 {amplitude2} delay2 {delay2}"))
    seq.append( maxlab.chip.DAC(dac1, 512-amplitude1) )
    seq.append( maxlab.chip.DAC(dac2, 512-amplitude2) )
    seq.append( maxlab.system.DelaySamples(delay1) )
    seq.append( maxlab.chip.DAC(dac1, 512+amplitude1) )
    seq.append( maxlab.system.DelaySamples(delay1) )
    seq.append( maxlab.chip.DAC(dac1, 512-amplitude1) )
    seq.append( maxlab.chip.DAC(dac2, 512+amplitude2) )
    seq.append( maxlab.system.DelaySamples(delay1) )
    seq.append( maxlab.chip.DAC(dac1, 512+amplitude1) )
    seq.append( maxlab.system.DelaySamples(delay1) )
    seq.append( maxlab.chip.DAC(dac1, 512) )
    seq.append( maxlab.chip.DAC(dac2, 512) )
    return seq

## We need to run an experiment per well, by looping over activate. 
EXP_WELLS = [0, 1, 2]

# PUT SOMETHING MEANINGFUL HERE
directory_name = "/home/mxwbio/Desktop/HAL/data/Tests/dac_test/"

WELL_CONFIGS = (random.sample(range(0, 100), 20), 
                random.sample(range(100, 200), 20),
                random.sample(range(200, 300), 20))  # List of configs <-- gonna have to add this.

print('Starting the experiment, T-Pain')
for wellID in EXP_WELLS:

    # PUT SOMETHING MEANINGFUL HERE
    file_name = "twoDACtest_well_" + str(wellID)

    maxlab.util.activate([wellID])
    maxlab.util.initialize()
    maxlab.send(maxlab.chip.Core().enable_stimulation_power(True))
    time.sleep(2)

    electrodes = WELL_CONFIGS[wellID] #BLANK - NEED TO READ IN CONFIG
    stimulation_electrodes = random.sample(WELL_CONFIGS[wellID], 2) # We need to select a subset 
    print(stimulation_electrodes)

    array = maxlab.chip.Array('stimulation')
    array.reset()
    array.clear_selected_electrodes( )
    array.select_electrodes( electrodes )
    array.select_stimulation_electrodes(stimulation_electrodes)
    array.route()

    stimulation_units = []

    for stim_el in stimulation_electrodes:
        array.connect_electrode_to_stimulation( stim_el )
        stim = array.query_stimulation_at_electrode( stim_el )
        print(array.query_amplifier_at_electrode(stim_el))
        if stim:
            stimulation_units.append( stim )
        else:
            print("No stimulation channel can connect to electrode: " + str(stim_el))

    maxlab.send(maxlab.chip.Amplifier().set_gain(512))
    array.download([wellID])    # Must be a list
    time.sleep(5)

    # maxlab.send_raw('stream_reset_command_counter')
    print("Intialized Well " + str(wellID) + ".")

    maxlab.util.offset()
    time.sleep(5)

    # First, poweroff all the stimulation units
    for stimulation_unit in range(0,32):
        # Stimulation Unit
        stim = maxlab.chip.StimulationUnit(stimulation_unit)
        stim.power_up(False)
        stim.connect(False)
        maxlab.send(stim)

    stimulation_unit_commands = []
    dac_count = 0
    for stimulation_unit in stimulation_units:
        print("Power up stimulation unit " + str(stimulation_unit))
        stim = maxlab.chip.StimulationUnit(stimulation_unit)
        stim.power_up(True).connect(True).set_voltage_mode().dac_source(dac_count)
        stimulation_unit_commands.append(stim)
        maxlab.send(stim)
        dac_count += 1
        print("Connected stimulation unit: " + str(stimulation_unit))
        time.sleep(2)
    print("All stim elects should be powered on!")

    sequence1 = maxlab.Sequence()
    append_stimulation_pulse(wellID, sequence1, 1, 0, 10, 4)
    sequence1.append(maxlab.system.DelaySamples(200))
    append_stimulation_pulse(wellID, sequence1, 1, 0, 10, 4)

    sequence2 = maxlab.Sequence()
    append_stimulation_pulse(wellID, sequence2, 2, 1, 10, 4)
    sequence2.append(maxlab.system.DelaySamples(200))
    append_stimulation_pulse(wellID, sequence2, 2, 1, 10, 4)

    sequence3 = maxlab.Sequence()
    append_conjoin_stimulation_pulse(wellID, sequence3, 3, 0, 1, 10, 4, 10, 4)
    sequence3.append(maxlab.system.DelaySamples(200))
    append_conjoin_stimulation_pulse(wellID, sequence3, 3, 0, 1, 10, 4, 10, 4)

    # Now we have to do the saving
    s = maxlab.Saving()
    s.open_directory(directory_name)
    s.start_file(file_name)
    s.group_delete_all()
    if wellID == 1 or wellID == 2:
        s.group_define(wellID, f"all_channels_{wellID}", list(range(1024)))
    else:
        s.group_define(wellID, f"all_channels_{wellID}", list(range(20)))

    print("recording...")
    s.start_recording([wellID]) # Must be a list

    time.sleep(10)
    print("Sending Seq 1...")
    sequence1.send()

    time.sleep(10)
    print("Sending Seq 2...")
    sequence2.send()

    time.sleep(10)
    print("Sending Seq 3...")
    sequence3.send()

    time.sleep(5)

    s.stop_recording()
    s.stop_file()
    s.group_delete_all()
    print("finished recording well: " + str(wellID))
    
    print("Done with well " + str(wellID) + "!") 
    time.sleep(5)