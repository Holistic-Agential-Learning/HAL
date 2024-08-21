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

rec_electrodes = []

all_configs = [
    "/home/mxwbio/configs/240819/buttonB_well5.cfg", #slow button  #TODO
    "/home/mxwbio/configs/240819/buttonA_well5.cfg", #fast button #TODO
    "/home/mxwbio/configs/240819/well5.cfg" #full (slow + fast + stim + read) #TODO
]

guidance = False #TODO Setup guidance here

def sync():
    context = zmq.Context()
    socket = context.socket(zmq.REP)
    socket.bind("tcp://*:5556")
    message = socket.recv()

    #  Send reply back to client
    socket.send(b"sync")

def plot():
    context = zmq.Context()
    socket = context.socket(zmq.SUB)
    socket.connect("tcp://localhost:5555")
    socket.setsockopt(zmq.SUBSCRIBE, b"")

    sync()

    buttons = []
    times = []
    stim_levels = []

    fig = plt.gcf()
    fig.show()
    fig.canvas.draw()
    plt.ylim(-1,11)
    plt.pause(1)

    while True:
        #  Wait for next request from client
        try:
            message = socket.recv()
        except KeyboardInterrupt:
            break

        if (message == b"stop"):
            break

        b,t,s = message.decode("utf-8").split(";")

        times.append(int(t))
        stim_levels.append(int(s))
        buttons.append(b)

        plt.plot(stim_levels, times, color = 'g', marker = 'o')
        plt.pause(0.01)
        fig.canvas.draw()

def thread_cpp(program_args):
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

    wells = [4] # TODO
    experiment_name = "test-progress" #TODO
    chip_id = "M07475" # TODO
    trial_path = hal.make_trial_folders_raw("/home/mxwbio/Desktop/HAL/data/frequency-game", experiment_name, chip_id, wells) #TODO
    
    mx.initialize()

    for well in wells:
        mx.activate([well]) 
        mx.set_primary_well(well)
        freq_electrodes = [8769, 18889, 5961, 16959] #TODO
        dec_guidance_electrodes = [] #TODO
        inc_guidance_electrodes = [] #TODO
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


        directory_name = f"{trial_path}/well{well}"
        file_name = experiment_name
        config_file_name = directory_name + "/" + file_name + f"_well_{well}_config.cfg"
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

        # TODO CHECK:
        #Setup stims with three difference DAC sources

        program_args = ["./bin/build/frequency-game", "--folder", directory_name]
        for i in range(len(new_buttons)):
            program_args.append(f"--config{i}")
            program_args.append(new_buttons[i])
        program_args.append("--well")
        program_args.append(str(well))
        program_args.append("--minutes")
        program_args.append(str(5)) # TODO set the number of minutes for the game
        program_args.append("--maxtwo")
        if guidance:
            program_args.append("--guidance")

        s = mx.Saving()
        s.open_directory(directory_name)
        s.start_file(file_name + "_well_" + str(well))
        hal.write_closed_loop_args(s, program_args)
        hal.write_stim_electrodes(s, stim_electrodes)

    
        s.group_delete_all()
        s.group_define(well, f"all_channels_{well}", list(range(1024)))
        print("recording... well " + str(well))
        s.start_recording([well])
        try:
            thread = threading.Thread(target = thread_cpp, args = [program_args])

            thread.start()

            plot()

            thread.join()


            mx.send(mx.Event(well, 1, 1, "end_subprocess 1"))
        except Exception as err: 
            print(f"An error occurred ({err}). Aborting...")

        ########################################################################

        s.stop_recording()
        s.stop_file()
        s.group_delete_all()
        print("finished recording")

    # subprocess.run(["./mail.sh"])