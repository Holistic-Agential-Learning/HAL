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
import bin.lib.py_src.config as cfg
import threading
import pickle
import bin.lib.py_src.plotter as plotter

#TODO optional variables if you want to use the same radius and density for all
# generated squares
sq_radius = 10
sq_steps = 2

# With this the button is width is: 2 * 17.5 um * sq_radius * sq_steps

#TODO configs
# the index of each element in the list corresponds to a well number
#
all_configs = [
    [],
    [],
    [],
    [(9711, sq_radius, sq_steps),
     (5687, sq_radius, sq_steps)], 
    [],
    [] 
]

#TODO indicates whether to simply read data, or to stimulate the buttons manually
live_chip = True

#TODO
wells = [3]

#TODO 
experiment_name = "live_chip"

#TODO
chip_id = "M07461" 

#TODO
maxtwo = True

#TODO 
experiment_time = 1

#TODO stimulation electrodes
a_electrodes = [
    [],
    [],
    [],
    [9711],
    [],
    []
]
b_electrodes = [
    [],
    [],
    [],
    [5687],
    [],
    []
]

#TODO desription
desc = "Verifying the button detection. Current releasing logic."

#TODO
sendEmail = False

def run_cpp(program_args):
    """Runs closed-loop program

    :param program_args: arguments of the program to run
    :type program_args: List[str]
    """
    try:
        subprocess.run(program_args)
    except KeyboardInterrupt:
        print("{__file__}: ^C signalled")
    except Exception as err:
        print(f"An error occurred: {err}")

def get_square(dims):
    return hal.get_electrode_square(dims[0], dims[1], dims[2])

def get_elecs(src):
    if isinstance(src, str):
        return cfg.read_config_elecs(src)
    else:
        return get_square(src)

def merge_configs(configs):
    s = set()
    for config in configs:
        elec_nums = get_elecs(config)
        for n in elec_nums:
            s.add(n)
    l = list(s)
    if (len(l) > 1020):
        print(f"WARNING: {len(l)} electrodes have been chosen--not all will be \
        routed")
    else:
        print(f"{len(l)} electrodes have been chosen")
    
    return list(s)



if __name__ == '__main__':
    trial_path = hal.make_trial_folders_raw("/home/mxwbio/Desktop/HAL/data/button_detection", experiment_name, chip_id, wells) #TODO
    
    mx.initialize()

    for well in wells:
        mx.activate([well])
        mx.set_primary_well(well)
        stim_electrodes = a_electrodes[well] + b_electrodes[well]
        rec_electrodes = stim_electrodes + merge_configs(all_configs[well])

        print(f"stimulation electrodes: {stim_electrodes}")

        time.sleep(5)
        if mx.send(mx.Core().enable_stimulation_power(True)) != "Ok":
            raise RuntimeError("The system didn't initialize correctly.")
        time.sleep(mx.Timing.waitInit)
        print(f"Initializing well {well}...")
        
        array = mx.Array(f"stimulation{well}")
        array.reset()
        array.clear_selected_electrodes()
        array.select_electrodes(rec_electrodes)
        array.select_stimulation_electrodes(stim_electrodes)
        array.route()
        array.download([well])
        
        a_units = hal.connect_stim_units_to_stim_electrodes(a_electrodes[well], array)
        b_units = hal.connect_stim_units_to_stim_electrodes(b_electrodes[well], array)

        directory_name, file_name, config_file_name = hal.get_file_names(well, experiment_name, trial_path)

        print(config_file_name)
        array.save_config(config_file_name)

        new_buttons = cfg.get_buttons(config_file_name, [get_elecs(all_configs[well][0]), get_elecs(all_configs[well][1])], directory_name)
        
        array.download([well]) 
        mx.offset() 
        mx.clear_events() 

        hal.power_up_stim_units(a_units, 0)
        hal.power_up_stim_units(b_units, 1)

        amp = 20

        stim_a = Stimulation(token="A", dac_source=0, amplitude=amp, phase=200, pulses_per_train=1, num_trains=1, pulse_interval=0,  pulse_train_interval=0, well=wells[0])
        stim_seq_a = stim_a.build_sequence()
        
        stim_b = Stimulation(token="B", dac_source=1, amplitude=amp, phase=200, pulses_per_train=1, num_trains=1, pulse_interval=0,  pulse_train_interval=0, well=wells[0])
        stim_seq_b = stim_b.build_sequence()

        a_pressed = mx.Sequence("A-pressed", persistent=False)
        del a_pressed
        a_pressed = mx.Sequence("A-pressed", persistent=True)
        a_pressed.append(mx.Event(well, 1, 5, "A pressed"))

        b_pressed = mx.Sequence("B-pressed", persistent=False)
        del b_pressed
        b_pressed = mx.Sequence("B-pressed", persistent=True)
        b_pressed.append(mx.Event(well, 1, 6, "B pressed"))


        program_args = ["./bin/build/button-detection", "--folder", directory_name]

        for i in range(len(new_buttons)):
            program_args.append(f"--config{i}")
            program_args.append(new_buttons[i])
        program_args.append("--well")
        program_args.append(str(well))
        program_args.append("--minutes")
        program_args.append(str(experiment_time))
        if live_chip: program_args.append("--live")
        if maxtwo: program_args.append("--maxtwo")

        s = mx.Saving()
        s.open_directory(directory_name)
        s.start_file(file_name)
        hal.write_exp_description(s, desc)
        hal.write_closed_loop_args(s, program_args)
        hal.write_stim_electrodes(s, stim_electrodes)

        s.group_delete_all()
        s.group_define(well, f"all_channels_{well}", list(range(1024)))
        s.start_recording([well])

        try:

            mx.send(mx.Event(well, 1, 2, f"start_experiment {well}"))

            run_cpp(program_args)

            mx.send(mx.Event(well, 1, 1, f"end_experiment {well}"))

        except KeyboardInterrupt:
            print("Keyboard Interrupt")
        except Exception as err: 
            print(f"An error occurred ({err}). Aborting...")


        s.stop_recording()
        s.stop_file()
        s.group_delete_all()
        print("finished recording - safe to exit.")

    if (sendEmail):
        subprocess.run(["./mail.sh"])
