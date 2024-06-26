import maxlab as mx
import matplotlib.pyplot as plt
import numpy as np

from typing import List
from time import sleep
from h5py import File
from pathlib import Path

import random
import sys



event_counter = 1


recording_dir = str("/home/mxwbio/")
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

    for i in range(0, 1000):
        mx.send(mx.Event(0, 1, event_counter, f"set_primary_well_{well} 0"))
        mx.send(set_primary_well())
        mx.send(mx.Event(0, 1, event_counter, f"set_primary_well_{well} 1"))

    s.stop_recording()
    sleep(mx.Timing.waitAfterRecording)
    s.stop_file()
    s.group_delete_all()