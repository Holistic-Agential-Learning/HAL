#!/usr/bin/env python
from typing import List

import random
import time

import json
import sys
import subprocess
import os

top_level_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.append(top_level_dir)

import maxlab as mx

from punish_reward.macro_punish import macro_punish
from punish_reward.macro_reward import macro_reward
from punish_reward.sine_reward import sine_reward

import bin.gui.GUI as GUI
from bin.lib.py_src.stimulation import Stimulation
import bin.lib.py_src.hal as hal
import bin.lib.py_src.config as cfg

rec_electrodes = []
a_and_b = [
    "/home/mxwbio/configs/240805/configB.cfg",
    "/home/mxwbio/configs/240805/configC.cfg"
]

# There are 4 button configs, each representing each quadrant of the chip:
#  
#   A  B
#   C  D
#
# Stimulation electrodes:
#   A: 442
#   B: 1095
#   C: 25304
#   D: 18891  <-- try to pick a new one

def merge_configs(configs):
    s = set()
    for config in configs:
        ret = GUI.read_config(config, False)
        elec_nums = ret[1]
        for n in elec_nums:
            s.add(n)

    return list(s)

if __name__ == '__main__':
    # configs = [sys.argv[i] for i in range(1, len(sys.argv))]

    wells = [0]
    file_name = "controller-test"

    stim_a = [1095]
    stim_b = [25304]


    trial_path = hal.make_trial_folders_raw("/home/mxwbio/Desktop/HAL/data/controller", file_name, 16365, [0])
    
    for well in wells:
        mx.activate([well])
        mx.set_primary_well(well)

        # stim_electrodes = exp_args["E_SELECTED"]
        rec_electrodes = merge_configs(a_and_b)
        
        does_stimulations = True

        mx.initialize()
        mx.send(mx.Core().enable_stimulation_power(True))

        # stimulation electrodes for configs/newconfig.cfg
        
        array = mx.Array("stimulation")
        array.reset()
        array.clear_selected_electrodes()
        #NOTE: stim_electrodes can include electrodes that aren't in rec_electrodes. In the future, maybe throw a warning if this is the case
        if not does_stimulations:
            print("not doing stimulations")
            stim_electrodes = []
        array.select_electrodes(stim_a + stim_b + rec_electrodes)
        # if does_stimulations:
        #     array.select_stimulation_electrodes(stim_electrodes)
        
        array.route()

        # stimulation setup here 
        if does_stimulations:
            stimulation_units_a = hal.connect_stim_units_to_stim_electrodes(stim_a, array)
            stimulation_units_b = hal.connect_stim_units_to_stim_electrodes(stim_b, array)


        directory_name = f"{trial_path}/well{well}"
        

        config_file_name = directory_name + "/" + file_name + f"_well_{well}_config.cfg"

        print(config_file_name)
        #save the config prior to running the code
        array.save_config(config_file_name)

        new_buttons = cfg.get_buttons(config_file_name, a_and_b, directory_name)

        array.download([well]) 

        mx.offset() 

        mx.clear_events() 

        if does_stimulations:
            hal.power_up_stim_units(stimulation_units_a, 0)
            hal.power_up_stim_units(stimulation_units_b, 1)


        stimA = Stimulation("A", 0, 10, 500, 10, 1, 1, 1, well = well) 
        stimA.build_sequence()
        stimB = Stimulation("B", 1, 10, 500, 10, 1, 1, 1, well = well)
        stimB.build_sequence()

        #Create start train and end sequences. TODO: LOOP THROUGH ALL WELLS AND DO THIS
        start_seq = mx.Sequence("before-training", persistent = False)
        del start_seq
        start_seq = mx.Sequence("before-training", persistent = True)
        start_seq.append(mx.Event(well, 1, 2, "before_training 1"))

        train_seq = mx.Sequence("training", persistent = False)
        del train_seq
        train_seq = mx.Sequence("training", persistent = True)
        train_seq.append(mx.Event(well, 1, 3, "training 1"))

        end_seq = mx.Sequence("after-training", persistent = False)
        del end_seq
        end_seq = mx.Sequence("after-training", persistent = True)
        end_seq.append(mx.Event(well, 1, 4, "after_training 1"))

        a_pressed = mx.Sequence("A-pressed", persistent=False)
        del a_pressed
        a_pressed = mx.Sequence("A-pressed", persistent=True)
        a_pressed.append(mx.Event(well, 1, 5, "A pressed"))

        b_pressed = mx.Sequence("B-pressed", persistent=False)
        del b_pressed
        b_pressed = mx.Sequence("B-pressed", persistent=True)
        b_pressed.append(mx.Event(well, 1, 6, "B pressed"))


        ##############################################################################

        program_args = ["./bin/build/controller-test", "--folder", directory_name]

        for i in range(len(a_and_b)):
            program_args.append(f"--config{i}")
            program_args.append(a_and_b[i])

        program_args.append("--well")

        program_args.append(str(well))


        s = mx.Saving()
        s.open_directory(directory_name)
        s.start_file(file_name + "_well_" + str(well))
        s.group_delete_all()

        hal.write_exp_description(s, "This program alternates stimulating A and B in order to test the controller class")
        s.write_assay_property("fano", "0.5")
        s.write_assay_property("z_score", "2")
        s.write_assay_property("firing_rate_threshold", "0.5")
        
        s.group_define(well, f"all_channels_{well}", list(range(1024)))
        # s.group_define(0, "smiley", list(range(1024)))
        print("recording... well " + str(well))
        s.start_recording([well])
        
        ############################################################################
        
        print("calling c++ script... well" + str(well))
        # This is the command to run (will last as long as the cpp files lasts)
        mx.send(mx.Event(well, 1, 1, "start_subprocess 1"))
        try:
            subprocess.run(program_args)
        except KeyboardInterrupt:
            print("start-maxlab.py: ^C signalled")
        except Exception as err:
            print(err)

        mx.send(mx.Event(well, 1, 1, "end_subprocess 1"))

        print("c++ script over...")
        ############################################################################

        s.stop_recording()
        s.stop_file()
        s.group_delete_all()
        print("finished recording")
