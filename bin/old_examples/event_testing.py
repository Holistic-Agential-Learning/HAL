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

import h5py
import pandas as pd

num_trials = 300
num_wells = 6


recording_dir = "/home/mxwbio/Desktop/HAL/data/event_testing/"
print(recording_dir)

file_name = "event_testing"


if __name__ == "__main__":

    filepath = Path(f"{recording_dir}/{file_name}.raw.h5")
    if filepath.is_file():
        print("save file already exists: deleting")
        filepath.unlink()

    wells = range(1)

    mx.activate(wells)
    mx.initialize()

    for well in wells:
        print("activating well " + str(well))
        mx.activate([well])
        array = mx.Array("well_" + str(well))
        array.reset()
        array.clear_selected_electrodes()
        array.select_electrodes(random.sample(range(0, 26400), 30))
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

    s.start_recording([0])

    sleep(5)

    mx.send(mx.Event(0, 1, 1, "hello 1"))
    mx.send(mx.Event(0, 1, 1, f"test 1"))
    mx.send(mx.Event(0, 1, 1, f"test 2"))
    mx.send(mx.Event(0, 1, 1, f"test 3"))

    mx.send(mx.Event(0, 1, 2, f"event 1"))

    mx.send(mx.Event(0, 1, 3, f"functional 1"))

    mx.send(mx.Event(0, 1, 4, f"functional text test 2"))

    mx.send(mx.Event(0, 1, 0, f"test 1"))

    mx.send(mx.Event(0, 1, 6, f"skip 1"))

    mx.send(mx.Event(0, 2, 1, f"different_type 1"))
    mx.send(mx.Event(0, 2, 7, f"different_type 1"))
    

    mx.send(mx.Event(0, 1, 0, "test 0"))
    mx.clear_events()



    mx.send(mx.Event(0, 1, 9, f"after 1"))
    mx.send(mx.Event(0, 1, 10, f"after 0"))
    mx.send(mx.Event(0, 1, 11, f"after -1"))

    sleep(5)


    s.stop_recording()
    s.stop_file()
    sleep(mx.Timing.waitAfterRecording)
    s.group_delete_all()














    print(str(filepath))

    with h5py.File(str(filepath), "r") as h5_file:
        h5_object = h5_file['wells']['well000']['rec0000']
        events = h5_object['events']
        events_arr= np.array(events)
        events_dataset = pd.DataFrame(events_arr)

    print("hi")
    print(events_dataset)
    for i in events_dataset.index:
        print(events_dataset.loc[i, :])
        print()