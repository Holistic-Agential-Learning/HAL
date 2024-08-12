#!/usr/bin/env python
from typing import List
import time
import sys
import subprocess
import os
top_level_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.append(top_level_dir)
import maxlab as mx
import bin.gui.GUI as GUI
from bin.lib.py_src.stimulation import Stimulation
import bin.lib.py_src.hal as hal

rec_electrodes = []

all_configs = [
    "/home/mxwbio/configs/240723/slow.cfg", #slow button  #TODO
    "/home/mxwbio/configs/240723/fast.cfg", #fast button #TODO
    "/home/mxwbio/configs/240724/full.cfg" #full (slow + fast + stim + read) #TODO
]

def merge_configs(configs):
    s = set()
    for config in configs:
        ret = GUI.read_config(config, False)
        elec_nums = ret[1]
        for n in elec_nums:
            s.add(n)
    return list(s)

if __name__ == '__main__':
    exp_args = {}
    exp_args['FOLDER'] = "/home/mxwbio/Desktop/HAL/data/burst_cl/{CHIPID}" #TODO
    exp_args['NAME'] = "burst_cl"
    exp_args['WELLS'] = [4] #TODO
    exp_args['-MAXTWO-'] = True
    trial_path = hal.make_trial_folders(exp_args)
        
    if exp_args['-MAXTWO-']:
        wells = exp_args['WELLS']
    else:
        wells = [0]
    
    mx.initialize()

    for well in wells:
        mx.activate([well]) 
        mx.set_primary_well(well)
        stim_electrodes = [13117,17437] #TODO
        rec_electrodes = merge_configs(all_configs)
        does_stimulations = True

        time.sleep(5)
        if mx.send(mx.Core().enable_stimulation_power(True)) != "Ok":
            raise RuntimeError("The system didn't initialize correctly.")
        time.sleep(mx.Timing.waitInit)
        print("Initializing wells...")
        
        array = mx.Array("stimulation")
        array.reset()
        array.clear_selected_electrodes()
        array.select_electrodes(rec_electrodes)
        array.select_stimulation_electrodes(stim_electrodes)
        array.route()

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
        array.save_config(config_file_name)
        
        array.download([well]) 
        mx.offset() 
        mx.clear_events() 

        if does_stimulations:
            for stimulation_unit in stimulation_units:
                stimulation = mx.StimulationUnit(stimulation_unit).power_up(True).connect(True).set_voltage_mode().dac_source(0)
                mx.send(stimulation)

        ##############################################################################

        # #define your new stims
        # print("Making stimulations...")
        # #30 sec each from 0.1 -> 1 -> 2 -> 10
        # stim_0p1 = Stimulation(token="stim_0p1", dac_source=0, amplitude=600, phase=400, pulses_per_train=1, num_trains=3, pulse_interval=0,  pulse_train_interval=9.9992, well=wells[0])
        # stim_01 = Stimulation(token="stim_01", dac_source=0, amplitude=600, phase=400, pulses_per_train=1, num_trains=30, pulse_interval=0,  pulse_train_interval=0.9992, well=wells[0])
        # stim_02 = Stimulation(token="stim_02", dac_source=0, amplitude=600, phase=400, pulses_per_train=1, num_trains=60, pulse_interval=0,  pulse_train_interval=0.4992, well=wells[0])
        # stim_03 = Stimulation(token="stim_03", dac_source=0, amplitude=600, phase=400, pulses_per_train=1, num_trains=90, pulse_interval=0,  pulse_train_interval=0.3325333333333333, well=wells[0])
        # stim_04 = Stimulation(token="stim_04", dac_source=0, amplitude=600, phase=400, pulses_per_train=1, num_trains=120, pulse_interval=0,  pulse_train_interval=0.2492, well=wells[0])
        # stim_05 = Stimulation(token="stim_05", dac_source=0, amplitude=600, phase=400, pulses_per_train=1, num_trains=150, pulse_interval=0,  pulse_train_interval=0.1992, well=wells[0])
        # stim_06 = Stimulation(token="stim_06", dac_source=0, amplitude=600, phase=400, pulses_per_train=1, num_trains=180, pulse_interval=0,  pulse_train_interval=0.16586666666666666, well=wells[0])
        # stim_07 = Stimulation(token="stim_07", dac_source=0, amplitude=600, phase=400, pulses_per_train=1, num_trains=210, pulse_interval=0,  pulse_train_interval=0.14205714285714288, well=wells[0])
        # stim_08 = Stimulation(token="stim_08", dac_source=0, amplitude=600, phase=400, pulses_per_train=1, num_trains=240, pulse_interval=0,  pulse_train_interval=0.1242, well=wells[0])
        # stim_09 = Stimulation(token="stim_09", dac_source=0, amplitude=600, phase=400, pulses_per_train=1, num_trains=270, pulse_interval=0,  pulse_train_interval=0.11031111111111111, well=wells[0])
        # stim_10 = Stimulation(token="stim_10", dac_source=0, amplitude=600, phase=400, pulses_per_train=1, num_trains=300, pulse_interval=0,  pulse_train_interval=0.0992, well=wells[0])

        # stim_0p1_seq = stim_0p1.build_sequence()
        # stim_01_seq = stim_01.build_sequence()
        # stim_02_seq = stim_02.build_sequence()
        # stim_03_seq = stim_03.build_sequence()
        # stim_04_seq = stim_04.build_sequence()
        # stim_05_seq = stim_05.build_sequence()
        # stim_06_seq = stim_06.build_sequence()
        # stim_07_seq = stim_07.build_sequence()
        # stim_08_seq = stim_08.build_sequence()
        # stim_09_seq = stim_09.build_sequence()
        # stim_10_seq = stim_10.build_sequence()

        # print(stim_0p1.get_duration())
        # print(stim_01.get_duration())
        # print(stim_02.get_duration())
        # print(stim_03.get_duration())
        # print(stim_04.get_duration())
        # print(stim_05.get_duration())
        # print(stim_06.get_duration())
        # print(stim_07.get_duration())
        # print(stim_08.get_duration())
        # print(stim_09.get_duration())
        # print(stim_10.get_duration())


        ##############################################################################

        stim = Stimulation(token="stim", dac_source=0, amplitude=600, phase=400, pulses_per_train=1, num_trains=1, pulse_interval=0,  pulse_train_interval=0, well=wells[0])
        stim_seq = stim.build_sequence()
        print(stim.get_duration())

        program_args = ["./bin/build/burst_cl", "--folder", directory_name]
        for i in range(len(all_configs)):
            program_args.append(f"--config{i}")
            program_args.append(all_configs[i])
        program_args.append("--well")
        program_args.append(str(well))

        s = mx.Saving()
        s.open_directory(directory_name)
        s.start_file(file_name + "_well_" + str(well))
        s.group_delete_all()
        s.group_define(well, f"all_channels_{well}", list(range(1024)))
        print("recording... well " + str(well))
        s.start_recording([well])
        
        
        print("calling c++ script... well" + str(well))
        mx.send(mx.Event(well, 1, 1, "start_subprocess 1"))
        try:
            subprocess.run(program_args)
        except KeyboardInterrupt:
            print("start-maxlab.py: ^C signalled")
        except Exception as err:
            print(err)

        #running this for 60 mins
        time.sleep(60 * 60)

        mx.send(mx.Event(well, 1, 1, "end_subprocess 1"))

        print("c++ script over...")
        ############################################################################

        s.stop_recording()
        s.stop_file()
        s.group_delete_all()
        print("finished recording")
