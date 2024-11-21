#!/usr/bin/env python

# tester.py
#
# This script is meant as a general setup script for basic closed-loop scripts,
# for either recording data or running HAL architecture tests
#
# Written by Trevor M. Sullivan
# November 2024

from typing import List
import sys
import subprocess
import os
top_level_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.append(top_level_dir)
import maxlab as mx
import bin.lib.py_src.hal as hal

#TODO
config = ""

#TODO
well = 0

#TODO script executable
script_name = "channel-window-test"

#TODO 
experiment_name = "button_verification"

#TODO
chip_id = "20551" 

#TODO
maxtwo = False

#TODO 
experiment_time = 0.5

#TODO desription
desc = "Verifying the button detection. New button releasing logic. window=1000 frames, std threshold=3"

#TODO
#
# emails to notify after the experiment ends
emails = []

def run_cpp(program_args):
    """Runs closed-loop program

    :param program_args: arguments of the program to run
    :type program_args: List[str]
    """
    try:
        subprocess.run(program_args)
    except KeyboardInterrupt:
        print(f"{__file__}: ^C signalled")
    except Exception as err:
        print(f"An error occurred: {err}")


if __name__ == '__main__':
    trial_path = hal.make_trial_folders_raw("/home/mxwbio/Desktop/HAL/data/button_detection", experiment_name, chip_id, wells) #TODO
    
    mx.initialize()

    array = hal.init_well(well, config, [])

    directory_name, file_name, config_file_name = hal.get_file_names(well, experiment_name, trial_path)

    print(config_file_name)
    array.save_config(config_file_name)
    
    array.download([well]) 
    mx.offset() 
    mx.clear_events() 

    program_args = [f"./bin/build/{script_name}", "--folder", directory_name]

    program_args.append("--config")
    program_args.append(config)

    program_args.append("--well")
    program_args.append(str(well))
    program_args.append("--minutes")
    program_args.append(str(experiment_time))
    if maxtwo: program_args.append("--maxtwo")

    s = mx.Saving()
    s.open_directory(directory_name)
    s.start_file(file_name)
    hal.write_exp_description(s, desc)
    hal.write_closed_loop_args(s, program_args)

    s.group_delete_all()
    s.group_define(well, f"all_channels_{well}", list(range(1024)))
    s.start_recording([well])

    try:
        run_cpp(program_args)


    except KeyboardInterrupt:
        print("Keyboard Interrupt")
    except Exception as err: 
        print(f"An error occurred ({err}). Aborting...")


    s.stop_recording()
    s.stop_file()
    s.group_delete_all()
    print("finished recording - safe to exit.")

    for email in emails:
        subprocess.run(["./mail.sh", email])
