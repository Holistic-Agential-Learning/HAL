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
    0: [7547,7647,20749,20848]
}
MINUTES = 1
THRESH = 0.2
STIM_RATE = 5 #stims per second?


if __name__ == '__main__':

    wells = [0]

    trial_path = hal.make_trial_folders_raw("/home/mxwbio/Desktop/HAL/data", "property", "12345", wells)

    
    
    for well in wells:
        mx.activate([well])
        mx.set_primary_well(well)

        rec_electrodes = [1000]
        
        does_stimulations = False

        mx.initialize()
        mx.send(mx.Core().enable_stimulation_power(True))

        # stimulation electrodes for configs/newconfig.cfg
        
        array = mx.Array(f"property{well}")
        array.reset()
        array.clear_selected_electrodes()
        #NOTE: stim_electrodes can include electrodes that aren't in rec_electrodes. In the future, maybe throw a warning if this is the case

        array.select_electrodes(STIM_ELECTRODES[well] + rec_electrodes)
        
        # array.select_stimulation_electrodes(STIM_ELECTRODES[well])
        
        array.route()
        

        # stimulation_units = hal.connect_stim_units_to_stim_electrodes(STIM_ELECTRODES[well], array)
        
        array.download([well])
        ############################################################################
        # WES LOOK HERE
        # change directory and file name of the recording here

        # Since the GUI makes a new experiment folder, we should probably save the data there
        # so that the params file and recording are in the same place. 
        # The date also needs to be updated in the param file to make sure it's the 
        # day the experiment was done. 

        directory_name = f"{trial_path}/well{well}"
        file_name = "property"  # <-- THIS NEEDS TO BE CHANGED !!!!

        config_file_name = directory_name + "/" + file_name + f"_well_{well}_config.cfg"

        print(config_file_name)
        #save the config prior to running the code
        array.save_config(config_file_name)
        ############################################################################

        mx.offset()

        mx.clear_events()
        

        s = mx.Saving()
        s.open_directory(directory_name)
        s.start_file(file_name + "_well_" + str(well))
        s.group_delete_all()
        
        s.group_define(well, f"all_channels_{well}", list(range(1024)))
        hal.write_stim_electrodes(s, STIM_ELECTRODES[0])
        hal.write_exp_description(s, "this eperiment tests the write_assay_property API call")
        s.write_assay_property("description:", "this is a test")
        s.write_assay_property("spaces?", "nospaces")
        s.write_assay_input("test", "super duper")
        s.write_assay_input("spacesAGAIN", "none")
        # s.group_define(0, "smiley", list(range(1024)))
        print("recording... well " + str(well))
        s.start_recording([well])
        
        ############################################################################
        # WES LOOK HERE
        # change timing pattern here
        # time.sleep(600)
        print("recording..." + str(well))
        # This is the command to run (will last as long as the cpp files lasts)
        time.sleep(10)

        # print("Ten minutes left")
        # time.sleep(600)
        ############################################################################

        s.stop_recording()
        s.stop_file()
        s.group_delete_all()
        print("finished recording")
