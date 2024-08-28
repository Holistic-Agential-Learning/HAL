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

plot_lock = threading.Lock()
data_condition = threading.Condition(plot_lock)
plot_data = []

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
    [(4817, sq_radius, sq_steps),
     (21089, sq_radius, sq_steps),
     "/home/mxwbio/configs/240827/M07480_DIV55_well2.cfg"],
    [],
    [],
    []
]

#TODO
wells = [2]

#TODO
experiment_name = "fast_plot"

#TODO
chip_id = "M07480" 

#TODO
maxtwo = True

#TODO toggle guidance system
guidance = False 

#TODO bounds for stim rates
max_frames_per_stim = 200000
min_frames_per_stim = 5000

#TODO ratio calculation time, experiment time, pre/post time, all in minutes
pre_exp_time = 0
ratio_calculation_time = 0
experiment_time = 10
post_exp_time = 5

#TODO stimulation electrodes
freq_electrodes = [
    [],
    [],
    [2031,6877,12599,23207],
    [],
    [],
    []
]

#TODO guidance electrodes
dec_guidance_electrodes = []
inc_guidance_electrodes = []

#TODO desription
desc = "Evan's test to try the new square button program + frequency game with big buttons."

#TODO
sendEmail = True

def sync():
    context = zmq.Context()
    socket = context.socket(zmq.REP)
    socket.bind("tcp://*:5556")
    try:
        message = socket.recv()
    except KeyboardInterrupt:
        return

    # Send message back to closed-loop program
    socket.send(b"sync")

def plot_producer():
    context = zmq.Context()
    socket = context.socket(zmq.SUB)
    socket.connect("tcp://localhost:5555")
    socket.setsockopt(zmq.SUBSCRIBE, b"")

    sync()

    while True:

        try:
            # print("waiting for message")
            message = socket.recv()
        except KeyboardInterrupt:
            break

        with data_condition:
            if (message == b"stop"):
                plot_data.append("stop")
                break

            b,t,s,r = message.decode("utf-8").split(";")

            plot_data.append([b, t, s, r])

            data_condition.notify()


def plot(file, min_frames, max_frames):
    producer = threading.Thread(target=plot_producer, args=[])

    producer.start()

    frame_rate = 10000.0 if maxtwo else 20000.0
    lower = frame_rate / max_frames
    upper = frame_rate / min_frames

    print(f"Max stim rate: {upper}")
    print(f"Min stim rate: {lower}")

    buttons = ["A", "B"]
    bar_colors = ["red", "blue"]
    button_counts = [0, 0]
    times = []
    stim_levels = []
    frequencies = []

    fig = plt.gcf()
    fig.show()

    freqpath = plt.subplot(311)
    freqpath.set_title("Stimulation Frequency")
    freqpath.set_ylabel("Stimulations per Second")
    freqpath.set_xlabel("Time (s)")
    freqpath.set_ylim(lower - 0.5,upper + 0.5)

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

    prev_rate = 0
    prev_space = 0
    prev_time = 0

    done = False
    try:
        while not done:

            with data_condition:
                while len(plot_data) == 0:
                    data_condition.wait()

                for item in plot_data:
                    if (item == "stop"):
                        done == True
                    else:
                        # b = item[0]
                        # t = item[1]
                        # s = item[2]
                        # r = item[3]
                        b, t, s, r = item
                        if (b == "A"):
                            button_counts[0] = button_counts[0] + 1
                        if (b == "B"):
                            button_counts[1] = button_counts[1] + 1  

                        times.append(float(t))
                        stim_levels.append(int(s))
                        frequencies.append(float(r))
                plot_data.clear()

            # stimulation frequency
            freqpath.plot(times, frequencies, color = 'g', marker = 'o')
            # freqpath.set_ylim(lower,upper)

            # Frequency World
            space.plot(times, stim_levels, color = 'purple', marker = 'o')
            # space.set_ylim(-1, 11)

            # Total Button Presses
            count.bar(buttons, button_counts, color=bar_colors)

            # prev_space = s
            # prev_rate = r
            # prev_time = t
            
            plt.tight_layout()
            
            fig.canvas.draw()
            plt.pause(0.0001)
        
        producer.join()
    except KeyboardInterrupt:
        print("plotter detected interrupt!")
    except Exception as err:
        print("ope")

    print("saving figure...")
    
    pickle.dump(fig, open(f"{file}.fig.pickle", 'wb'))

def thread_cpp(program_args):
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
    trial_path = hal.make_trial_folders_raw("/home/mxwbio/Desktop/HAL/data/frequency-game", experiment_name, chip_id, wells) #TODO
    
    mx.initialize()

    for well in wells:
        mx.activate([well])
        mx.set_primary_well(well)
        stim_electrodes = freq_electrodes[well] + dec_guidance_electrodes + inc_guidance_electrodes
        rec_electrodes = freq_electrodes[well] + merge_configs(all_configs[well])

        print(f"stimulation electrodes: {stim_electrodes}")

        time.sleep(5)
        if mx.send(mx.Core().enable_stimulation_power(True)) != "Ok":
            raise RuntimeError("The system didn't initialize correctly.")
        time.sleep(mx.Timing.waitInit)
        print(f"Initializing well {well}...")
        
        array = mx.Array(f"stimulation{well}")
        array.reset()
        array.clear_selected_electrodes()
        array.select_electrodes(stim_electrodes + rec_electrodes)
        array.select_stimulation_electrodes(stim_electrodes)
        array.route()
        array.download([well])
        
        freq_units = hal.connect_stim_units_to_stim_electrodes(freq_electrodes[well], array)
        inc_units = hal.connect_stim_units_to_stim_electrodes(inc_guidance_electrodes, array)
        dec_units = hal.connect_stim_units_to_stim_electrodes(dec_guidance_electrodes, array)

        directory_name, file_name, config_file_name = hal.get_file_names(well, experiment_name, trial_path)

        print(config_file_name)
        array.save_config(config_file_name)

        new_buttons = cfg.get_buttons(config_file_name, [get_elecs(all_configs[well][0]), get_elecs(all_configs[well][1])], directory_name)
        
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

            # plot on the main thread (since Matplotlib only works on the main 
            # thread)
            plot(directory_name + "/" + file_name, min_frames_per_stim, max_frames_per_stim)

            thread.join()

            mx.send(mx.Event(well, 1, 1, f"end_experiment {well}"))

            print(f"Recording for {post_exp_time}...")

            time.sleep(60 * post_exp_time)   # Post
        except KeyboardInterrupt:
            print("Keyboard Interrupt")
        except Exception as err: 
            print(f"An error occurred ({err}). Aborting...")

        ########################################################################

        

        s.stop_recording()
        s.stop_file()
        s.group_delete_all()
        print("finished recording - safe to exit.")

    if (sendEmail):
        subprocess.run(["./mail.sh"])
