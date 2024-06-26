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


recording_dir = str(Path(os.getcwd(), "..", "..", "data", "timing"))
file_name = "stim"


if __name__ == "__main__":

    filepath = Path(f"{recording_dir}/{file_name}.raw.h5")
    if filepath.is_file():
        print("save file already exists: deleting")
        filepath.unlink()

    wells = range(0, 6)

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

    s.group_define(0, "all_channels", list(range(1024)))

    mx.send(mx.Event(0, 1, 1, f"test nodelay_set_primary_well"))

    event_counter = 1
    for i in range(0, num_trials):
        well = i%6
        mx.send(mx.Event(0, 1, event_counter, f"set_primary_well 0 well {well}"))
        mx.send(mx.set_primary_well(well))
        mx.send(mx.Event(0, 1, event_counter, f"set_primary_well_{well} 1 well {well}"))
        event_counter += 1


    sleep(5)
    mx.send(mx.Event(0, 2, 1, f"test delay_set_primary_well"))
    event_counter = 1
    for i in range(0, num_trials):
        well = i%6
        mx.send(mx.Event(0, 2, event_counter, f"set_primary_well 0 well {well}"))
        mx.send(mx.set_primary_well(well))
        mx.send(mx.Event(0, 2, event_counter, f"set_primary_well 1 well {well}"))
        event_counter += 1
        sleep(1)


    sleep(5)
    mx.send(mx.Event(0, 3, 1, f"test delay_activate_wells"))
    event_counter = 1
    for i in range(0, num_trials):
        num_wells = random.sample(range(1, 7), 1)
        activation_wells = random.sample(range(0, 6), num_wells)
        mx.send(mx.Event(0, 3, event_counter, f"activate_wells 0 num_wells {num_wells}"))
        mx.send(mx.activate(activation_wells))
        mx.send(mx.Event(0, 3, event_counter, f"activate_wells 1 num_wells {num_wells}"))
        event_counter += 1
        sleep(1)
    
    sleep(5)
    mx.send(mx.Event(0, 4, 1, f"test nodelay_activate_wells"))
    event_counter = 1
    for i in range(0, num_trials):
        well = i%6
        mx.send(mx.Event(0, 4, event_counter, f"activate_wells 0 well {well}"))
        mx.send(mx.activate(activation_wells))
        mx.send(mx.Event(0, 4, event_counter, f"activate_wells 1 well {well}"))
        event_counter += 1


    sleep(5)
    mx.send(mx.Event(0, 5, 1, f"test events"))
    event_counter = 1
    for i in range(0, num_trials):
        well = i%6
        mx.send(mx.Event(0, 5, event_counter, f"event 0"))
        mx.send(mx.Event(0, 5, event_counter, f"event 1"))
        event_counter += 1






    s.stop_recording()
    sleep(mx.Timing.waitAfterRecording)
    s.stop_file()
    s.group_delete_all()
