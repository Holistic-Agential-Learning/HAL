import maxlab as mx
import matplotlib.pyplot as plt
import numpy as np

from typing import List
from time import sleep
from h5py import File
from pathlib import Path

import random
import os
import sys

num_trials = 1000
num_wells = 6


recording_dir = str(Path(os.path.dirname(__file__), "..", "..", "data", "timing"))
recording_dir = "/home/mxwbio/Desktop/HAL/data/timing/"
print(recording_dir)

file_name = "stim_test_2"


if __name__ == "__main__":

    filepath = Path(f"{recording_dir}/{file_name}.raw.h5")
    if filepath.is_file():
        print("save file already exists: deleting")
        filepath.unlink()

    wells = range(0, num_wells)

    mx.activate(wells)
    mx.initialize()

    for well in wells:
        print("activating well " + str(well))
        mx.activate([well])
        array = mx.Array("well_" + str(well))
        array.reset()
        array.clear_selected_electrodes()
        array.select_electrodes(random.sample(range(0, 26400), 1020))
        array.route()
        array.download([well])
        sleep(mx.Timing.waitAfterDownload)
    

    mx.activate(wells)
    mx.offset()
    sleep(5)

    mx.clear_events()



    

    s = mx.Saving()
    s.open_directory(recording_dir)
    s.start_file(file_name)

    s.group_delete_all()

    s.group_define(0, "all_channels0", list(range(1024)))
    s.group_define(1, "all_channels1", list(range(1024)))
    s.group_define(2, "all_channels2", list(range(1024)))
    s.group_define(3, "all_channels3", list(range(1024)))
    s.group_define(4, "all_channels4", list(range(1024)))
    s.group_define(5, "all_channels5", list(range(1024)))

    s.start_recording(wells)
    print("testing nodelay set primary well")
    #mx.send(mx.Event(0, 1, 1, f"test nodelay_set_primary_well"))

    event_counter = 1
    for i in range(0, num_trials):
        well = i%num_wells
        mx.send(mx.Event(0, 1, event_counter, f"set_primary_well 0 well {well}"))
        mx.set_primary_well(well)
        mx.send(mx.Event(0, 1, event_counter, f"set_primary_well_{well} 1 well {well}"))
        event_counter += 1


    sleep(5)
    mx.send(mx.Event(0, 3, 1, f"test delay_activate_wells"))
    print("testing delay activate wells")

    event_counter = 1
    for i in range(0, num_trials):
        num_wells_activated = random.sample(range(1, num_wells + 1), 1)[0]
        activation_wells = random.sample(wells, num_wells_activated)
        print(activation_wells)
        mx.send(mx.Event(0, 3, event_counter, f"activate_wells 0 num_wells {num_wells_activated}"))
        mx.activate(activation_wells)
        mx.send(mx.Event(0, 3, event_counter, f"activate_wells 1 num_wells {num_wells_activated}"))
        event_counter += 1
        sleep(0.2)




    sleep(5)
    print("testing delay set primary well")

    mx.send(mx.Event(0, 2, 1, f"test delay_set_primary_well"))
    event_counter = 1
    for i in range(0, num_trials):
        well = i%num_wells
        mx.send(mx.Event(0, 2, event_counter, f"set_primary_well 0 well {well}"))
        mx.set_primary_well(well)
        mx.send(mx.Event(0, 2, event_counter, f"set_primary_well 1 well {well}"))
        event_counter += 1
        sleep(0.2)
    
    sleep(5)
    print("testing nodelay activate wells")

    mx.send(mx.Event(0, 4, 1, f"test nodelay_activate_wells"))
    event_counter = 1
    for i in range(0, num_trials):
        well = i%num_wells
        mx.send(mx.Event(0, 4, event_counter, f"activate_wells 0 well {well}"))
        mx.activate(activation_wells)
        mx.send(mx.Event(0, 4, event_counter, f"activate_wells 1 well {well}"))
        event_counter += 1


    sleep(5)
    print("testing events")
    mx.send(mx.Event(0, 5, 1, f"test events"))
    event_counter = 1
    for i in range(0, num_trials):
        well = i%num_wells
        mx.send(mx.Event(0, 5, event_counter, f"event 0"))
        mx.send(mx.Event(0, 5, event_counter, f"event 1"))
        event_counter += 1






    s.stop_recording()
    s.stop_file()
    sleep(mx.Timing.waitAfterRecording)
    s.group_delete_all()
