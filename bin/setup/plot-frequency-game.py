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

rec_electrodes = []

all_configs = [
    "/home/mxwbio/configs/240823/Left Button.cfg", #slow button  #TODO
    "/home/mxwbio/configs/240823/Right Button.cfg", #fast button #TODO
    "/home/mxwbio/configs/240823/NS Config Well 5.cfg" #full (slow + fast + stim + read) #TODO
]

#TODO
wells = [5]

#TODO
experiment_name = "initial_test_with_plotting_60min"

#TODO
chip_id = "M07475" 

#TODO toggle guidance system
guidance = False 

#TODO ratio calculation time, experiment time, pre/post time, all in minutes
ratio_calculation_time = 5
experiment_time = 60
pre_exp_time = 10
post_exp_time = 10

#TODO stimulation electrodes
freq_electrodes = [2493,5521,6103,6499]

#TODO guidance electrodes
dec_guidance_electrodes = []
inc_guidance_electrodes = []

#TODO times

def sync():
    context = zmq.Context()
    socket = context.socket(zmq.REP)
    socket.bind("tcp://*:5556")
    try:
        message = socket.recv()
    except KeyboardInterrupt:
        return

    #  Send reply back to client
    socket.send(b"sync")

def plot(file):
    context = zmq.Context()
    socket = context.socket(zmq.SUB)
    socket.connect("tcp://localhost:5555")
    socket.setsockopt(zmq.SUBSCRIBE, b"")

    sync()

    buttons = ["A", "B"]
    bar_colors = ["red", "blue"]
    button_counts = [0, 0]
    times = []
    stim_levels = []
    frequencies = []

    fig = plt.gcf()
    fig.show()

    freqpath = plt.subplot(211)
    freqpath.set_title("Stimulation Frequency")
    freqpath.set_ylabel("Stimulations per Second")
    freqpath.set_xlabel("Time (s)")
    freqpath.set_ylim(0,5)

    space = plt.subplot(312)
    space.set_title("Frequency World")
    space.set_ylabel("Stimulation Level")
    space.set_xlabel("Time")
    space.set_ylim(-1, 11)

    count = plt.subplot(313)
    count.set_title("Total Button Presses")
    count.set_ylabel("Count")
    count.set_xlabel("Buttons")

    fig.tight_layout()
    fig.canvas.draw()

    print("plot initialized")

    while True:
        #  Wait for next request from client
        try:
            print("waiting for message")
            message = socket.recv()
        except KeyboardInterrupt:
            break

        if (message == b"stop"):
            break

        b,t,s,r = message.decode("utf-8").split(";")

        print(f"{b};{t};{s};{r}")

        if (b == "A"):
            button_counts[0] = button_counts[0] + 1
        if (b == "B"):
            button_counts[1] = button_counts[1] + 1  

        times.append(float(t))
        stim_levels.append(int(s))
        frequencies.append(float(r))

        # stimulation frequency
        freqpath.plot(times, frequencies, color = 'g', marker = 'o')

        # Frequency World
        space.plot(times, frequencies, color = 'purple', marker = 'o')

        # Total Button Presses
        count.bar(buttons, button_counts, color=bar_colors)
        
        plt.tight_layout()
        
        fig.canvas.draw()
        plt.pause(0.01)

    print("saving figure...")
    
    pickle.dump(fig, open(f"{file}.fig.pickle", 'wb'))

def thread_cpp(program_args):
    """Runs closed-loop program on another thread

    :param program_args: arguments of the program to run
    :type program_args: List[str]
    """
    try:
        subprocess.run(program_args)
    except KeyboardInterrupt:
        print("{__file__}: ^C signalled")
    except Exception as err:
        print(f"An error occurred: {err}")

def merge_configs(configs):
    s = set()
    for config in configs:
        ret = GUI.read_config(config, False)
        elec_nums = ret[1]
        for n in elec_nums:
            s.add(n)
    return list(s)

if __name__ == '__main__':
    trial_path = hal.make_trial_folders_raw("/home/mxwbio/Desktop/HAL/data/frequency-game", experiment_name, chip_id, wells) #TODO
    
    mx.initialize()

    for well in wells:
        mx.activate([well]) 
        mx.set_primary_well(well)
        stim_electrodes = freq_electrodes # + dec_guidance_electrodes + inc_guidance_electrodes
        rec_electrodes = freq_electrodes + merge_configs(all_configs)
        print(len(rec_electrodes))
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
        
        freq_units = hal.connect_stim_units_to_stim_electrodes(freq_electrodes, array)
        inc_units = hal.connect_stim_units_to_stim_electrodes(inc_guidance_electrodes, array)
        dec_units = hal.connect_stim_units_to_stim_electrodes(dec_guidance_electrodes, array)

        directory_name, file_name, config_file_name = hal.get_file_names(well, experiment_name, trial_path)

        print(config_file_name)
        array.save_config(config_file_name)

        new_buttons = cfg.get_buttons(config_file_name, [all_configs[0], all_configs[1]], directory_name)
        
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
        program_args.append("--ratio-time")
        program_args.append(str(ratio_calculation_time))
        program_args.append("--maxtwo")
        if guidance:
            program_args.append("--guidance")

        s = mx.Saving()
        s.open_directory(directory_name)
        s.start_file(file_name)
        hal.write_exp_description(s, "We're doing a 60 minute test to see what happens with frequency game. Should have plots, but bottom right bad.")
        hal.write_closed_loop_args(s, program_args)
        hal.write_stim_electrodes(s, stim_electrodes)

        s.group_delete_all()
        s.group_define(well, f"all_channels_{well}", list(range(1024)))
        print("recording... well " + str(well))
        s.start_recording([well])

        time.sleep(60 * pre_exp_time)   # Pre

        try:
            thread = threading.Thread(target = thread_cpp, args = [program_args])

            thread.start()

            plot(directory_name + "/" + file_name)

            thread.join()

            mx.send(mx.Event(well, 1, 1, "end_subprocess 1"))
        except KeyboardInterrupt:
            print("Keyboard Interrupt")
        except Exception as err: 
            print(f"An error occurred ({err}). Aborting...")

        ########################################################################

        time.sleep(60 * post_exp_time)   # Post

        s.stop_recording()
        s.stop_file()
        s.group_delete_all()
        print("finished recording")

    subprocess.run(["./mail.sh"])
