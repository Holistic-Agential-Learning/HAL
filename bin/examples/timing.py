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
    print(str(mx.query_DAC_lsb_mV()))
    sys.exit()

    filepath = Path(f"{recording_dir}/{file_name}.raw.h5")
    if filepath.is_file():
        print("save file already exists: deleting")
        filepath.unlink()


    mx.initialize()


    wells = range(0, 5)

    for well in wells:
        mx.activate([well])
        array = mx.Array()
        array.select_electrodes(random.sample(range(0, 26400), 1020))
        array.route()
        array.download([well])
        sleep(mx.Timing.waitAfterDownload)
    

    mx.activate(wells)
    mx.offset()
    sleep(5)

    mx.clear_events()





    # s = mx.Saving()
    # s.open_directory(recording_dir)
    # s.start_file(file_name)

    # s.group_define(0, "all_channels", list(range(1024)))

    print(mx.query_DAC_lsb_mV)

    for i in range(0, 1000):
        mx.send(mx.Event(1, 1, event_counter, f"set_primary_well start"))

        mx.send(mx.Event(1, 1, event_counter, f"set_primary_well end"))
