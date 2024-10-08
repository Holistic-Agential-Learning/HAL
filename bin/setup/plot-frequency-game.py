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
import zmq
import matplotlib.pyplot as plt
import pickle
import bin.lib.py_src.plotter as plotter

# TODO optional variables if you want to use the same radius and density for all
# generated squares
sq_radius = 10
sq_steps = 2

# With this the button is width is: 2 * 17.5 um * sq_radius * sq_steps

# TODO configs
# the index of each element in the list corresponds to a well number
#
all_configs = [
    ["/home/mxwbio/configs/240802/buttonA.cfg",    #inhib
     "/home/mxwbio/configs/240802/buttonB.cfg"],  #excit
    [(26203, sq_radius, sq_steps),    #inhib
     (13015, sq_radius, sq_steps),    #excit
     "/home/mxwbio/configs/240828/15h06m13s.cfg"],
    [(4817, sq_radius, sq_steps),
     (21089, sq_radius, sq_steps),
     "/home/mxwbio/configs/240828/15h06m16s.cfg"],
    [], # not this oen
    [(10795, sq_radius, sq_steps),    #excite
     (1609, sq_radius, sq_steps),    #inhib
     "/home/mxwbio/configs/240828/15h06m24s.cfg"],
    [] # not this one
]

# TODO
wells = [0]

# TODO
#
# full path to parent directory of experiment data
#
# data for each trial will be saved in "parent_dir/experiment_name/chip_id/date/trial"
parent_dir = "/home/mxwbio/Desktop/HAL/data/frequency-game"

# TODO 
experiment_name = "NES-test"

# TODO
chip_id = "20551" 

# TODO
maxtwo = False

# TODO toggle guidance system
guidance = True 

# TODO bounds for stim rates
max_frames_per_stim = 200000
min_frames_per_stim = 5000

# TODO ratio calculation time, experiment time, pre/post time, all in minutes
pre_exp_time = 0
experiment_time = 1.8
post_exp_time = 0

# TODO stimulation electrodes
freq_electrodes = [
    [6180, 21747],
    [3071,6101,12717,22857],
    [2463,13433,15393,21091],
    [],
    [15281,21965,22247,23639],
    []
]

# TODO guidance electrodes
dec_guidance_electrodes = [
    [6182],
    [],
    [],
    [],
    [],
    []
]
inc_guidance_electrodes = [
    [21305],
    [],
    [],
    [],
    [],
    []
]

# TODO 
#
# experiment description
desc = ""

# TODO
sendEmail = False


def thread_cpp(program_args):
    """Runs closed-loop program, intended to be used by a separate thread IF 
    using the live plotter (since Matplotlib works best on the main thread)

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
    """
    Returns an electrode square based on a dimensions tuple

    :param dims: "dimensions" of the square: center electrode, "radius", and 
                 number of steps
    :type dims: Tuple[int, int, int]
    :return: electrodes corresponding to the square
    :rtype: List[int]
    """
    return hal.get_electrode_square(dims[0], dims[1], dims[2])

def get_elecs(src):
    """
    Returns electrodes of a configuration file OR a dimensions tuple

    :param src: configuration file or square "dimensions" tuple
    :type src: Tuple[int, int, int] | str
    :return: list of electrodes
    :rtype: List[int]
    """
    if isinstance(src, str):
        return cfg.read_config_elecs(src)
    else:
        return get_square(src)

def merge_configs(configs):
    """
    Merges electrodes from multiple sources

    :param configs: list of configuration files or square dimensions
    :type configs: List[str | Tuple[int, int, int]]
    :return: list of electrodes
    :rtype: List[int]
    """
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
    trial_path = hal.make_trial_folders_raw(parent_dir, experiment_name, chip_id, wells)
    
    mx.initialize()

    for well in wells:
        mx.activate([well])
        mx.set_primary_well(well)
        stim_electrodes = freq_electrodes[well] + dec_guidance_electrodes[well] + inc_guidance_electrodes[well]
        rec_electrodes = freq_electrodes[well] + merge_configs(all_configs[well])

        print(f"stimulation electrodes: {stim_electrodes}")

        time.sleep(5)
        if mx.send(mx.Core().enable_stimulation_power(True)) != "Ok":
            raise RuntimeError("The system didn't initialize correctly.")
        time.sleep(mx.Timing.waitInit)
        print(f"Initializing well {well}...")

        # manually connect and power stimulation elecs/units since we are using 
        # different DACS
        array = hal.init_well(well, rec_electrodes, stim_electrodes, connect=False, power_up=False)
        
        freq_units = hal.connect_stim_units_to_stim_electrodes(freq_electrodes[well], array)
        inc_units = hal.connect_stim_units_to_stim_electrodes(inc_guidance_electrodes[well], array)
        dec_units = hal.connect_stim_units_to_stim_electrodes(dec_guidance_electrodes[well], array)

        directory_name, file_name, config_file_name = hal.get_file_names(well, experiment_name, trial_path)

        print(config_file_name)
        array.save_config(config_file_name)

        new_buttons = cfg.get_buttons(config_file_name, [get_elecs(all_configs[well][0]), get_elecs(all_configs[well][1])], directory_name)
        
        # TODO TODO
        #
        # test this -- it should be in init_well; does it matter if it happens
        # before or after connecting stimulation units?
        array.download([well]) 
        mx.offset() 
        mx.clear_events() 

        hal.power_up_stim_units(freq_units, 0)
        hal.power_up_stim_units(inc_units, 1)
        hal.power_up_stim_units(dec_units, 2)

        stim = Stimulation(token="stim", dac_source=0, amplitude=300, phase=200, pulses_per_train=1, num_trains=1, pulse_interval=0,  pulse_train_interval=0, well=wells[0])
        stim_seq = stim.build_sequence()
        print(stim.get_duration())

        inc_stim = Stimulation(token="inc_guidance", dac_source=1, amplitude=100, phase=200, pulses_per_train=1, num_trains=1, pulse_interval=0,  pulse_train_interval=0, well=wells[0])
        inc_stim_seq = inc_stim.build_sequence()
        print(inc_stim.get_duration())

        dec_stim = Stimulation(token="dec_guidance", dac_source=2, amplitude=100, phase=200, pulses_per_train=1, num_trains=1, pulse_interval=0,  pulse_train_interval=0, well=wells[0])
        dec_stim_seq = dec_stim.build_sequence()
        print(dec_stim.get_duration())

        program_args = ["./bin/build/plot-frequency-game", "--folder", directory_name]

        for i in range(len(new_buttons)):
            program_args.append(f"--config{i}")
            program_args.append(new_buttons[i])
        program_args.append("--well")
        program_args.append(str(well))
        program_args.append("--minutes")
        program_args.append(str(experiment_time))
        if maxtwo:
            program_args.append("--maxtwo")
        program_args.append("--lower")
        program_args.append(str(min_frames_per_stim))
        program_args.append("--upper")
        program_args.append(str(max_frames_per_stim))
        if guidance:
            program_args.append("--guidance")

        s = mx.Saving()
        s.open_directory(directory_name)
        s.start_file(file_name)
        hal.write_exp_description(s, desc)
        hal.write_closed_loop_args(s, program_args)
        hal.write_stim_electrodes(s, stim_electrodes)

        s.group_delete_all()
        s.group_define(well, f"all_channels_{well}", list(range(1024)))
        s.start_recording([well])

        print(f"Recording well {well} for {pre_exp_time} minutes...")

        try:
            time.sleep(60 * pre_exp_time)   # Pre

            # run closed-loop program on another thread
            thread = threading.Thread(target = thread_cpp, args = [program_args])

            mx.send(mx.Event(well, 1, 5, f"start_experiment {well}"))
            thread.start()

            # plot on the main thread (since Matplotlib only works on the main thread)
            p = plotter.Plotter(directory_name + "/" + file_name, maxtwo, min_frames_per_stim, max_frames_per_stim)
            p.plot_frequency_game()

            thread.join()

            mx.send(mx.Event(well, 1, 1, f"end_experiment {well}"))

            print(f"Recording for {post_exp_time}...")

            time.sleep(60 * post_exp_time)   # Post
        except KeyboardInterrupt:
            print("Keyboard Interrupt")
        except Exception as err: 
            print(f"An error occurred ({err}) while recording for well {well}. Aborting...")

        ########################################################################

        

        s.stop_recording()
        s.stop_file()
        s.group_delete_all()
        print("finished recording - safe to exit.")

    if (sendEmail):
        subprocess.run(["./mail.sh"])
