#!/usr/bin/env python
from typing import List


import random
import time
import json
import sys
import subprocess
import os



import maxlab as mx

top_level_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.append(top_level_dir)

import bin.gui.GUI as GUI
from bin.lib.py_src.stimulation import Stimulation
import bin.lib.py_src.hal as hal


STIM_ELECTRODES = {
    0: [2907,4365,22677,23713],
    2: [3315,6127,22413,22671]
}
MINUTES = 60
THRESH = 0.2
STIM_RATE = 5 #stims per second?


if __name__ == '__main__':
    print("running start-maxlab...")
    if len(sys.argv) > 1:
        f = open(sys.argv[1], "r")
        exp_args = json.load(f)
        f.close()
    else:
        f = open(GUI.start_gui(), "r")
        exp_args = json.load(f)
        f.close()

    trial_path = hal.make_trial_folders(exp_args)
    program_file = open("./bin/gui/programs.json", "r")
        
    if exp_args['-MAXTWO-']:
        wells = exp_args['WELLS']
    else:
        wells = [0]
    
    for well in wells:
        mx.activate([well])
        mx.set_primary_well(well)

        rec_electrodes = exp_args["CONFIGS"][str(well)]["E_NUMS"]
        
        does_stimulations = True

        mx.initialize()
        mx.send(mx.Core().enable_stimulation_power(True))

        # stimulation electrodes for configs/newconfig.cfg
        
        array = mx.Array(f"stimulation{well}")
        array.reset()
        array.clear_selected_electrodes()
        #NOTE: stim_electrodes can include electrodes that aren't in rec_electrodes. In the future, maybe throw a warning if this is the case

        array.select_electrodes(STIM_ELECTRODES[well] + rec_electrodes)
        
        array.select_stimulation_electrodes(STIM_ELECTRODES[well])
        
        array.route()
        

        stimulation_units = hal.connect_stim_units_to_stim_electrodes(STIM_ELECTRODES[well], array)
        
        array.download([well])
        ############################################################################
        # WES LOOK HERE
        # change directory and file name of the recording here

        # Since the GUI makes a new experiment folder, we should probably save the data there
        # so that the params file and recording are in the same place. 
        # The date also needs to be updated in the param file to make sure it's the 
        # day the experiment was done. 

        directory_name = f"{trial_path}/well{well}"
        file_name = exp_args["NAME"]  # <-- THIS NEEDS TO BE CHANGED !!!!

        config_file_name = directory_name + "/" + file_name + f"_well_{well}_config.cfg"

        print(config_file_name)
        #save the config prior to running the code
        array.save_config(config_file_name)
        ############################################################################

        mx.offset()

        mx.clear_events() 



        for stimulation_unit in stimulation_units:
            stimulation = mx.StimulationUnit(stimulation_unit).power_up(True).connect(True).set_voltage_mode().dac_source(0)
            print("Stimulation unit " + str(stimulation_unit) + " routed")
            mx.send(stimulation)

        # WHAT IS THIS???
        # s = mx.Sequence('test_seq', persistent=False)

        
        # stop_seq = mx.Sequence('stop_seq', persistent=True)
        # stop_seq.append(mx.DelaySamples(20000))

        # conda activate jkts
        # /home/mxwbio/MaxLab/python/lib/python3.10/site-packages/maxlab

        single_pulse = Stimulation("pulse", 0, 50, 200, 1, 1, 10, 1, well = well)
        duration = single_pulse.get_duration()
        single_pulse.build_sequence(initial_delay = 0)



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

        # converted_params["NUM_TRAINS"] = int(experiment_params["NUM_TRAINS"])
        # converted_params["TRAIN_INTERVAL"] = int(float(experiment_params["TRAIN_INTERVAL"]) * 20000)
        
        ##############################################################################

        program_args = [f"./bin/build/stim_removal", "2>", "ERR_LOG", "--config", config_file_name, "--folder", directory_name, "--pulse_duration", str(duration)]
        if exp_args['-MAXTWO-']:
            program_args.append("--maxtwo")
        
        #TODO: put them on top to change from run to run
        program_args.append("--threshold")
        program_args.append(str(THRESH))
        program_args.append("--minutes")
        program_args.append(str(MINUTES))
        program_args.append("--well")
        program_args.append(str(well))
        program_args.append("--stim_rate")
        program_args.append(str(STIM_RATE))

        

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
        mx.send(mx.Event(well, 1, 1, "start_subprocess 1"))
        try:
            subprocess.run(program_args)
        except KeyboardInterrupt:
            print("start-maxlab.py: ^C signalled")
        except Exception as err:
            print(err)

        mx.send(mx.Event(well, 1, 1, "end_subprocess 1"))

        # print("Ten minutes left")
        print("c++ script over...")
        # time.sleep(600)
        ############################################################################

        s.stop_recording()
        s.stop_file()
        s.group_delete_all()
        print("finished recording")
