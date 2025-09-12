'''
Caitlin testing
'''

import os, sys
import time
import subprocess

import maxlab as mx

top_level_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.append(top_level_dir)

import bin.lib.py_src.hal as hal
from bin.lib.py_src.stimulation import Stimulation

# User Input
wells = [0,1] # list of wells between 0-5
save_dir = '' # ex. "/tmp"
h5_filename = 'closed_loop_mulitwell_test'
rec_elecs = [[],
             []]
stim_elecs = [[0,0], # first electrode = trigger, second = closed-loop
              [0,0]]

def append_stimulation_pulse(seq: mx.Sequence, amplitude: int, event_id: int) -> mx.Sequence:
    seq.append(mx.Event(0, 1, event_id, f"event_id {event_id}"))
    seq.append(mx.DAC(0, 512 - amplitude))
    seq.append(mx.DelaySamples(4))
    seq.append(mx.DAC(0, 512 + amplitude))
    seq.append(mx.DelaySamples(4))
    seq.append(mx.DAC(0, 512))
    return seq

if __name__=='__main__':

    # Initializations from maxwell example not in HAL
    mx.send(mx.Amplifier().set_gain(512))
    # For the purpose of this example, we set the spike detection
    # threshold a bit higher, to avoid/reduce false positives.
    # Set detection threshold to 8.5x std of noise
    mx.set_event_threshold(8.5)

    detection_electrodes = []
    sequences = []

    s = mx.Saving() # a single h5 with multiple wells as different groups
    s.open_directory(save_dir)
    s.start_file(h5_filename)
    s.group_delete_all()

    # Well-specific initializations
    for i,well in enumerate(wells):

        array, stimulation_units = hal.init_well(well, rec_elecs[i], stim_elecs[i], dac_source = 0, power_up=False)
        
        # Select detection electrodes to detect trigger activity - passed into C++ script
        detection_electrodes.append(array.query_amplifier_at_electrode(stim_elecs[0][0] + 1))

        cmd_power_trigger_stim = mx.StimulationUnit(stimulation_units[0]).power_up(True).connect(True).set_voltage_mode().dac_source(0)
        cmd_power_down_trigger_stim = mx.StimulationUnit(stimulation_units[0]).power_up(False)
        cmd_power_cl_stim = mx.StimulationUnit(stimulation_units[1]).power_up(True).connect(True).set_voltage_mode().dac_source(0)
        cmd_power_down_cl_stim = mx.StimulationUnit(stimulation_units[1]).power_up(False)

        # Trigger pulse (simulating a spike)
        sequence1 = mx.Sequence(f'trigger_well{well}', persistent=True)
        sequence1.append(cmd_power_trigger_stim)
        append_stimulation_pulse(sequence1, 6, 1)
        sequence1.append(cmd_power_down_trigger_stim)

        # Closed-loop pulse
        sequence2 = mx.Sequence(f'stimulation_well{well}', persistent=True)
        sequence2.append(cmd_power_cl_stim)
        append_stimulation_pulse(sequence2, 10, 2)
        sequence2.append(cmd_power_down_cl_stim)

        sequences.append([sequence1, sequence2])

        s.group_define(well, f"all_channels_{well}", list(range(1024)))

    # Start C++ script
    try:
        subprocess.run(f"./bin/build/process_spike_events {detection_electrodes[0]}") # use well 1 detection electrode # TODO: adapt C++ script to stimulate both wells  
    except KeyboardInterrupt:
        print("start-maxlab.py: ^C signalled")
    except Exception as err:
        print(err)

    s.start_recording(wells)

    print("Start recording")

    # Deliver 200 stimulation pulses to trigger electrode
    for rep in range(200):
        sequences[0][0].send() # send trigger sequence for well0
        sequences[1][0].send() # send trigger sequence for well1
        time.sleep(1.5)

    print("Stop recording")

    s.stop_recording()

    time.sleep(mx.Timing.waitAfterRecording)

    s.stop_file()
    s.group_delete_all()