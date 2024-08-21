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

rec_electrodes = []
a_and_b = [
    "/home/mxwbio/configs/240723/configA.cfg",
    "/home/mxwbio/configs/240723/config.cfg"
]
configs = [
    "/home/mxwbio/configs/240724/configA.cfg",
    "/home/mxwbio/configs/240724/configB.cfg",
    "/home/mxwbio/configs/240724/full.cfg"
]


# load recording electrodes and stimulation electrodes
def config_electrodes(electrode_config, stim_electrodes):
    
    # recording electrodes config file
    array = mx.Array("stimulation")
    array.load_config(electrode_config)

    array.reset()
    # array.clear_selected_electrodes()
    # array.select_electrodes()
    array.select_stimulation_electrodes(stim_electrodes)
    array.route()

    return array

# create stimulation pulse (from maxlab tutorial page)
def create_stim_pulse(seq: mx.Sequence, amplitude: int, phase: int) -> mx.Sequence:
    seq.append(mx.DAC(0, 512 - amplitude))
    seq.append(mx.DelaySamples(phase))
    seq.append(mx.DAC(0, 512 + amplitude))
    seq.append(mx.DelaySamples(phase))
    seq.append(mx.DAC(0, 512))
    return seq

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

    exp_args = {}
    exp_args['FOLDER'] = "/home/mxwbio/Desktop/HAL/data/controller-test"
    exp_args['NAME'] = "controller-test"
    exp_args['WELLS'] = [0]
    exp_args['-MAXTWO-'] = False


    trial_path = hal.make_trial_folders(exp_args)
        
    if exp_args['-MAXTWO-']:
        wells = exp_args['WELLS']
    else:
        wells = [0]
    
    for well in wells:
        mx.activate([well])
        mx.set_primary_well(well)

        # stim_electrodes = exp_args["E_SELECTED"]
        stim_electrodes = [13117,17437]
        rec_electrodes = merge_configs(configs)
        
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
        array.select_electrodes(stim_electrodes + rec_electrodes)
        # if does_stimulations:
        #     array.select_stimulation_electrodes(stim_electrodes)
        
        array.route()
        # array = config_electrodes("configs/test_config.cfg", stim_electrodes)

        # stimulation setup here 
        if does_stimulations:
            stimulation_units = []
            for stim_el in stim_electrodes:
                array.connect_electrode_to_stimulation(stim_el)
                stim = array.query_stimulation_at_electrode(stim_el)
                if len(stim) == 0:
                    raise RuntimeError(
                        f"No stimulation channel can connect to electrode: \
                            {str(stim_el)}"
                    )
                stim_unit_int = int(stim)
                if stim_unit_int in stimulation_units:
                    raise RuntimeError(
                        f"Two electrodes connected to the same stim unit.\
                                    This is not allowed. Please Select a \
                                        neighboring electrode of {stim_el}!"
                    )
                else:
                    stimulation_units.append(stim_unit_int)


        directory_name = f"{trial_path}/well{well}"
        file_name = exp_args["NAME"]

        config_file_name = directory_name + "/" + file_name + f"_well_{well}_config.cfg"

        print(config_file_name)
        #save the config prior to running the code
        array.save_config(config_file_name)
        


        array.download([well]) 

        mx.offset() 

        mx.clear_events() 

        if does_stimulations:
            for stimulation_unit in stimulation_units:
                stimulation = mx.StimulationUnit(stimulation_unit).power_up(True).connect(True).set_voltage_mode().dac_source(0)
                mx.send(stimulation)

        reward_seq = sine_reward("reward")
        #reward_seq = macro_reward("reward")
        for i in range(0,1000):
            var_name = f"punish{i}"
            globals()[var_name] = macro_punish("INTER_PHASE", f"punish{i}")

        # These stimulations were used for tests to confirm that the controller
        # /new channel window features worked
        #
        # stimA = Stimulation("A", 0, 10, 500, 10, 1, 1, 1, well = well) 
        # stimA.build_sequence()
        # stimB = Stimulation("B", 1, 10, 500, 10, 1, 1, 1, well = well)
        # stimB.build_sequence()

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

        ##############################################################################

        program_args = ["./bin/build/control", "--folder", directory_name]

        for i in range(len(configs)):
            program_args.append(f"--config{i}")
            program_args.append(configs[i])

        program_args.append("--well")

        program_args.append(str(well))

        

        s = mx.Saving()
        s.open_directory(directory_name)
        s.start_file(file_name + "_well_" + str(well))
        s.group_delete_all()
        
        s.group_define(well, f"all_channels_{well}", list(range(1024)))
        # s.group_define(0, "smiley", list(range(1024)))
        print("recording... well " + str(well))
        s.start_recording([well])
        
        ############################################################################
        
        print("calling c++ script... well" + str(well))
        # This is the command to run (will last as long as the cpp files lasts)
        # mx.send(mx.Event(well, 1, 1, "start_subprocess 1"))
        # try:
        #     subprocess.run(program_args)
        # except KeyboardInterrupt:
        #     print("start-maxlab.py: ^C signalled")
        # except Exception as err:
        #     print(err)
        time.sleep(60 * 20)

        mx.send(mx.Event(well, 1, 1, "end_subprocess 1"))

        print("c++ script over...")
        ############################################################################

        s.stop_recording()
        s.stop_file()
        s.group_delete_all()
        print("finished recording")
