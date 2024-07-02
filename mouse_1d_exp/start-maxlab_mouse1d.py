#!/usr/bin/env python
from typing import List

import random
import time
import bin.gui.GUI as GUI
import json
import sys
import subprocess
import os

import numpy as np



import maxlab as mx

from bin.lib.stimulation import *
from world_stimulation import *



WORLD = "10000100"
POSITION = 4
LEFT_STIM_ELECTRODES = []
RIGHT_STIM_ELECTRODES = []
CENTER_STIM_ELECTRODES = []

############################################################################
# INSTRUCTIONS FOR WES
#
#   The next two lines of code are the stimulation electrodes and the 
# recording channel config. Change these whenever you load in a new neuron
# culture

# stim_electrodes = [3401, 8683, 14833, 22325]
rec_electrodes = []


# start by running this program with 
#       
#       ./start-maxlab.py examples/one_big.json
#
# You can modify one_big.json to change the stimulation
# 
# When this program prints "start C++ file now", run the following command in 
# another terminal
#
#       ./stim-burst-side
#
# If you want to change the sleeping patterns or where the recording file is 
# saved, scroll to the bottom part of this file and follow the instructions
# there.
############################################################################




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

if __name__ == '__main__':
    if len(sys.argv) > 1:
        f = open(sys.argv[1], "r")
        exp_params = json.load(f)
    else:
        exp_params = GUI.start_gui()

    program_file = open("./bin/gui/programs.json", "r")
    program_parameters = json.load(program_file)[exp_params["-PROGRAM-"]]["parameters"]
        
    if exp_params['-MAXTWO-']:
        wells = exp_params['WELLS']
    else:
        wells = [0]
    
    for well in wells:
        mx.activate([well])
        mx.set_primary_well(well)

        stim_electrodes = exp_params["E_SELECTED"]
        rec_electrodes = exp_params["CONFIGS"][str(well)]["E_NUMS"]


        stim_electrodes = LEFT_STIM_ELECTRODES + RIGHT_STIM_ELECTRODES + CENTER_STIM_ELECTRODES
        
        # does_stimulations = True
        # if exp_params["STIMULATIONS"] == {}:
        #     does_stimulations = False

        mx.initialize()
        mx.send(mx.Core().enable_stimulation_power(True))

        # stimulation electrodes for configs/newconfig.cfg
        
        array = mx.Array("stimulation")
        array.reset()
        array.clear_selected_electrodes()
        #NOTE: stim_electrodes can include electrodes that aren't in rec_electrodes. In the future, maybe throw a warning if this is the case
        
        array.select_electrodes(stim_electrodes + rec_electrodes)
        array.select_stimulation_electrodes(stim_electrodes)
        array.route()
        # array = config_electrodes("configs/test_config.cfg", stim_electrodes)

        # stimulation setup here 
        
        left_stimulation_units = []
        right_stimulation_units = []
        center_stimulation_units = []
        stimulation_units = []
        for stim_el in LEFT_STIM_ELECTRODES:
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
                left_stimulation_units.append(stim_unit_int)
                stimulation_units.append(stim_unit_int)

        for stim_el in RIGHT_STIM_ELECTRODES:
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
                right_stimulation_units.append(stim_unit_int)
                stimulation_units.append(stim_unit_int)

        for stim_el in CENTER_STIM_ELECTRODES:
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
                center_stimulation_units.append(stim_unit_int)
                stimulation_units.append(stim_unit_int)
        
        assert left_stimulation_units + right_stimulation_units + center_stimulation_units == center_stimulation_units
        ############################################################################
        # WES LOOK HERE
        # change directory and file name of the recording here

        # Since the GUI makes a new experiment folder, we should probably save the data there
        # so that the params file and recording are in the same place. 
        # The date also needs to be updated in the param file to make sure it's the 
        # day the experiment was done. 

        directory_name = exp_params["FOLDER"]
        file_name = exp_params["NAME"]  # <-- THIS NEEDS TO BE CHANGED !!!!

        config_file_name = directory_name + "/" + file_name + f"_well_{well}_config.cfg"

        print(config_file_name)
        #save the config prior to running the code
        array.save_config(config_file_name)
        ############################################################################


        array.download([well])

        mx.offset()

        mx.clear_events() 

        for stimulation_unit in left_stimulation_units:
            stimulation = mx.StimulationUnit(stimulation_unit).power_up(True).connect(True).set_voltage_mode().dac_source(0)
            mx.send(stimulation)

        for stimulation_unit in right_stimulation_units:
            stimulation = mx.StimulationUnit(stimulation_unit).power_up(True).connect(True).set_voltage_mode().dac_source(1)
            mx.send(stimulation)
        
        for stimulation_unit in center_stimulation_units:
            stimulation = mx.StimulationUnit(stimulation_unit).power_up(True).connect(True).set_voltage_mode().dac_source(2)
            mx.send(stimulation)

        # WHAT IS THIS???
        # s = mx.Sequence('test_seq', persistent=False)

        #CREATE STIMULI THAT ENCODE DISTANCE. PLEASE ENSURE THAT ALL OF THESE HAVE SIMILAR DURATIONS!!!!!!!
        objects_of_interest = {
            "1": ObjectDistanceParams(len(WORLD), np.linspace(80, 0, 4), 200, 5, 1, 10, 1)
        }

        build_world_stimulation(WORLD, objects_of_interest, exp_params['-MAXTWO-'], well)

        #CREATE STIMULI THAT ENCODE LOCATIONS
        object_stimuli = {
            "1": Stimulation("1", 2, 200, 500, 10, 3, 10, 1, maxtwo = exp_params['-MAXTWO-'], well = well)
        }

        for stimulation in object_stimuli.values():
            stimulation.create_sequence()


        #Create start train and end sequences. TODO: LOOP THROUGH ALL WELLS AND DO THIS
        start_seq = mx.Sequence("before-training", persistent = False)
        del start_seq
        start_seq = mx.Sequence("before-training", persistent = True)
        start_seq.append(mx.Event(well, 1, 1, "before_training 1"))

        train_seq = mx.Sequence("training", persistent = False)
        del train_seq
        train_seq = mx.Sequence("training", persistent = True)
        train_seq.append(mx.Event(well, 1, 2, "training 1"))

        end_seq = mx.Sequence("after-training", persistent = False)
        del end_seq
        end_seq = mx.Sequence("after-training", persistent = True)
        end_seq.append(mx.Event(well, 1, 3, "after_training 1"))

        # converted_params["NUM_TRAINS"] = int(experiment_params["NUM_TRAINS"])
        # converted_params["TRAIN_INTERVAL"] = int(float(experiment_params["TRAIN_INTERVAL"]) * 20000)
        
        ##############################################################################

        program_args = [f"./bin/build/{exp_params['PROGRAM_EXEC']}", "2>", "ERR_LOG", "--config", config_file_name]
        if exp_params['-MAXTWO-']:
            program_args.append("--maxtwo")

        for name in program_parameters.keys():
            if exp_params[name] != "":
                program_args.append(program_parameters[name]["arg"])
                program_args.append(exp_params[name])
        
        program_args.append("--well")

        program_args.append(str(well))

        program_args.append("--world")
        program_args.append(WORLD)
        program_args.append("--loc")
        program_args.append(POSITION)

        

        s = mx.Saving()
        s.open_directory(directory_name)
        s.start_file(file_name + "_well_" + str(well))
        s.group_delete_all()
        
        s.group_define(well, f"all_channels_{well}", list(range(1024)))
        # s.group_define(0, "smiley", list(range(1024)))
        print("recording... well " + str(well))
        s.start_recording([well])
        
        ############################################################################
        # WES LOOK HERE
        # change timing pattern here
        # time.sleep(600)
        print("calling c++ script... well" + str(well))
        # This is the command to run (will last as long as the cpp files lasts)
        try:
            subprocess.run(program_args)
        except KeyboardInterrupt:
            print("start-maxlab.py: ^C signalled")
        except Exception as err:
            print(err)

        # print("Ten minutes left")
        print("c++ script over...")
        # time.sleep(600)
        ############################################################################

        s.stop_recording()
        s.stop_file()
        s.group_delete_all()
        print("finished recording")
