#!/usr/bin/env python
import sys
import os
sys.path.append(os.path.dirname(__file__) + "/..")
from typing import List, Iterable
from pathlib import Path


import random
import time
import json

import subprocess

import numpy as np


import maxlab as mx
from bin.lib.stimulation import *

import matplotlib.pyplot as plt

from h5py import File




class ObjectDistanceParams:
    def __init__(self, world_size: int, amplitudes: list = [], phases: list = [], pulses_per_train: list = [], num_trains: list = [], pulse_intervals: list = [], pulse_train_intervals: list = []):
        """Stores how stimulus parameters change with distance. 
            If distance is greater than the length of a given parameter list, the parameter value defaults to 0.
            If any argument 

        Args:
            world_size(int): the maximum distance that can be observed in the world. Safest to just use the size of the world.
            amplitudes (_type_): _description_
            phases (_type_): _description_
            pulses_per_train (_type_): _description_
            num_trains (_type_): _description_
            pulse_intervals (_type_): _description_
            pulse_train_intervals (_type_): _description_
        """
        def assign_list_num(size, list_or_num):
            ret = [0] * size
            if not isinstance(list_or_num, Iterable):
                for i in range(0, size):
                    ret[i] = list_or_num
            else:
                ret[0:min(len(list_or_num), size)] = list_or_num[0:min(len(list_or_num), size)]

            return ret

        self.amplitudes = assign_list_num(world_size, amplitudes)
        self.phases = assign_list_num(world_size, phases)
        self.pulses_per_train = assign_list_num(world_size, pulses_per_train)
        self.num_trains = assign_list_num(world_size, num_trains)
        self.pulse_intervals = assign_list_num(world_size, pulse_intervals)
        self.pulse_train_intervals = assign_list_num(world_size, pulse_train_intervals)


#parameters for stimulations:
    #amplitude, phase, pulses_per_train, num_trains, pulse_interval, pulse_train_interval
def build_distance_stimuli(world: str, object_distance_params: dict, maxtwo: bool = False, well: int = 0)->List[ArbitraryStimulation]:
    """Function to create Sequences for every single position in the world. Stores sequences with tokens of the form f"loc{i}_distance".

    Args:
        world (str): A string representing the 1D world.
        objects (dict): A dictionary of stimulus parameters.
        maxtwo (bool, optional): Whether or not the code is being run on the MaxTwo. Defaults to False.
        well (int, optional): The well number. Defaults to 0.
        list_mode (bool, optional): Whether or not to output a list instead of a sequence. Defaults to False.
    
    Returns:
        list of sequences, indexed by the location in the world.
    """
    #each stimulus 
    stimuli = list()
    world_size = len(world)
    for i, loc in enumerate(world):
        leftward_stim = None
        rightward_stim = None
        #find nearest object to the left
        for j in range(1, world_size):
            leftward_loc = world[i-j]
            if leftward_loc in object_distance_params.keys():
                print(f"loc {i}: object {leftward_loc} found {j} spaces to the left")
                distance_index = j-1
                obj_params = object_distance_params[leftward_loc]
                leftward_stim = Stimulation(f"l{i}", 0, 
                                            amplitude = obj_params.amplitudes[distance_index], 
                                            phase = obj_params.phases[distance_index],
                                            pulses_per_train = obj_params.pulses_per_train[distance_index],
                                            num_trains = obj_params.num_trains[distance_index],
                                            pulse_interval = obj_params.pulse_intervals[distance_index],
                                            pulse_train_interval = obj_params.pulse_train_intervals[distance_index],
                                            maxtwo = maxtwo,
                                            well = well
                                            )
                
                break   

        #find nearest object to the right
        for j in range(1, world_size):
            rightward_loc = world[(i+j) % world_size]
            if rightward_loc in object_distance_params.keys():
                print(f"loc {i}: object {rightward_loc} found {j} spaces to the right")
                distance_index = j-1
                obj_params = object_distance_params[rightward_loc]

                rightward_stim = Stimulation(f"r{i}", 1, 
                                            amplitude = obj_params.amplitudes[distance_index], 
                                            phase = obj_params.phases[distance_index],
                                            pulses_per_train = obj_params.pulses_per_train[distance_index],
                                            num_trains = obj_params.num_trains[distance_index],
                                            pulse_interval = obj_params.pulse_intervals[distance_index],
                                            pulse_train_interval = obj_params.pulse_train_intervals[distance_index],
                                            maxtwo = maxtwo,
                                            well = well
                                            )
                
                break   

        assert leftward_stim and rightward_stim, "no objects found"

        combined_stimuli = Stimulation.combine_stimuli(leftward_stim, rightward_stim, f"loc{i}_distance", maxtwo=maxtwo)
    
        stimuli.append(combined_stimuli)
    return stimuli

if __name__ == '__main__':

    print("hello world")
    
    world = "abc123"
    obj_params = {
        "2": ObjectDistanceParams(len(world), 3),
        "3": ObjectDistanceParams(len(world))

    }
    stimuli = build_distance_stimuli("abc123", obj_params)

    for i in stimuli:
        print(i.sequence_list)
        print(i.duration)
        print(i.token)
    print(stimuli)



#maybe we rely on outside code to create the stimuli when at a given location?