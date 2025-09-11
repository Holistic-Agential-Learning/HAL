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
h5_filename = 'closed_loop_test_cgrass'
rec_elecs = []
stim_elecs = [] # chosen from rec_elecs

trigger_electrode = 0 # choose from stim_elecs
closed_loop_electrode = 0 # choose from stim_elecs


if __name__=='__main__':

    mx.set_event_threshold(5.2)

    s = mx.Saving() # a single h5 with multiple wells as different groups
    s.open_directory(save_dir)
    s.start_file(h5_filename)
    s.group_delete_all()


    # Initialization 
    for i,well in enumerate(wells):
        array = hal.init_well(well, rec_elecs[i], stim_elecs[i], dac_source = 0)

        # Trigger pulse (simulating a spike)
        trigger = Stimulation("trigger{well}", dac_source=0, amplitude=250, phase=200, pulses_per_train=1, num_trains=1,
                            pulse_interval=1, pulse_train_interval=1, well=well)
        trigger_duration = trigger.get_duration() #TODO: check that this function uses the correct fps for m1 chip - used for pulse_duration in burst_trainer.cpp input 
        trigger.build_sequence(initial_delay=0)

        # Closed loop pulse (simulating a spike)
        closed_loop = Stimulation("closed_loop{well}", dac_source=0, amplitude=250, phase=200, pulses_per_train=1, num_trains=1,
                            pulse_interval=1, pulse_train_interval=1, well=well)
        closed_loop_duration = closed_loop.get_duration() #TODO: check that this function uses the correct fps for m1 chip - used for pulse_duration in burst_trainer.cpp input 
        closed_loop.build_sequence(initial_delay=0)

        for well in wells:
            s.group_define(well, f"all_channels_{well}", list(range(1024)))

    s.start_recording(wells)

    print("Start recording")

    try:
        subprocess.run(f"./bin/build/burst_trainer")
    except KeyboardInterrupt:
        print("start-maxlab.py: ^C signalled")
    except Exception as err:
        print(err)
    
    print("Stop recording")

    s.stop_recording()

    time.sleep(mx.Timing.waitAfterRecording) #NOTE: Is this necessary?

    s.stop_file()
    s.group_delete_all()