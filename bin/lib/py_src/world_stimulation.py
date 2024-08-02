#!/usr/bin/env python
import sys
import os
sys.path.append(os.path.dirname(__file__) + "/..")
from typing import List, Iterable, Dict
from pathlib import Path


import random
import time
import json

import subprocess

import numpy as np


import maxlab as mx
from stimulation import *

import matplotlib.pyplot as plt

from h5py import File




class ObjectDistanceParams:
    def __init__(self, world_size: int, amplitudes: List[float] | float = [], phases: List[float] | float  = [], pulses_per_train: List[int] | int  = [], num_trains: List[int] | int  = [], pulse_intervals: List[float] | float  = [], pulse_train_intervals: List[float] | float  = []):
        """Stores parameters for stimuli delivered to an embodied culture in a 1D world.

        :param world_size: The maximum distance observable by the culture in a 1D world.
        :type world_size: int
        :param amplitudes: A list of amplitudes of stim pulses for each unit away an object of interest is, in mV. If a float is passed, the same amplitude is used for all distances. defaults to []
        :type amplitudes: List[float] | float, optional
        :param phases: A list of phases of stim pulses for each unit away an object of interest is, in us. If a float is passed, the same phase is used for all distances. defaults to []
        :type phases: List[float] | float, optional
        :param pulses_per_train: A list of pulses per train of stimuli for each unit away an object of interest is. If an int is passed, the same number of pulses per train is used for all distances. defaults to []
        :type pulses_per_train: List[int] | int, optional
        :param num_trains: A list of numbers of trains of stimuli for each unit away an object of interest is. If an int is passed, the same number of number of trains is used for all distances. defaults to []
        :type num_trains: List[int] | int, optional
        :param pulse_intervals: A list of pulse intervals for each stimuli for each unit away an object of interest is. If a float is passed, the same pulse interval is used for all distances. defaults to []
        :type pulse_intervals: List[float] | float, optional
        :param pulse_train_intervals: A list of pulse train intervals for each stimuli for each unit away an object of interest is. If a float is passed, the same pulse train interval is used for all distances. defaults to []
        :type pulse_train_intervals: List[float] | float, optional
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
def build_distance_stimuli(world: str, object_distance_params: Dict[str, ObjectDistanceParams], maxtwo: bool = False, well: int = 0)->List[ArbitraryStimulation]:
    """Function to create Sequences for every single position in the world. Stores sequences with tokens of the form f"loc{i}_distance".

    :param world: A string representing the 1D world.
    :type world: ``str``
    :param object_distance_params: A dictionary of ObjectDistanceParams, each indexed by its corresponding "location of interest" in the world.
    :type object_distance_params: ``dict``
    :param maxtwo: Whether or not the code is being run on the MaxTwo, defaults to False
    :type maxtwo: ``bool``, optional
    :param well: The well number. Defaults to 0.
    :type well: ``int``, optional
    :return: list of Stimulation sequences, indexed by the location in the world.
    :rtype: ``List[ArbitraryStimulation]``
    """
    #each stimulus 
    stimuli = list()
    world_size = len(world)
    for i, loc in enumerate(world):
        leftward_stim = Stimulation(f"l{i}", 0, amplitude = 0, phase = 0, pulses_per_train = 0, num_trains = 0, pulse_train_interval = 0, pulse_interval = 0, well = well)
        rightward_stim = Stimulation(f"l{i}", 1, amplitude = 0, phase = 0, pulses_per_train = 0, num_trains = 0, pulse_train_interval = 0, pulse_interval = 0, well = well)
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
                                            well = well
                                            )
                
                break   

        #find nearest object to the right
        for j in range(1, world_size + 1):
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
                                            well = well
                                            )
                
                break   

        #assert leftward_stim and rightward_stim, "no objects found"

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
        for j in i.sequence_list:
            print(j.properties)
        print(i.duration)
        print(i.token)
    print(stimuli)



#maybe we rely on outside code to create the stimuli when at a given location?