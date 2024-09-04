#!/usr/bin/env python

from typing import List

import random
import time

import json
import sys
import subprocess
import os

top_level_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.append(top_level_dir)

import maxlab as mx

from punish_reward.macro_punish import macro_punish
from punish_reward.macro_reward import macro_reward
from punish_reward.sine_reward import sine_reward

import bin.gui.GUI as GUI
from bin.lib.py_src.stimulation import Stimulation
import bin.lib.py_src.hal as hal
import bin.lib.py_src.config as cfg


if __name__ == '__main__':
    well = 0
    mx.activate([well])
    mx.set_primary_well(well)
    
    mx.initialize()
    mx.send(mx.Core().enable_stimulation_power(True))
    
    array = mx.Array("square")
    array.reset()
    array.clear_selected_electrodes()

    rec_electrodes1 = hal.get_electrode_square(10000, 5, 2)
    rec_electrodes2 = hal.get_electrode_square(5000, 6, 1)

    array.select_electrodes(rec_electrodes1 + rec_electrodes2)
    
    array.route()

    array.download([well]) 

    mx.offset() 
