#!/usr/bin/env python
import sys
import os
sys.path.append(os.path.dirname(__file__) + "/..")
from typing import List

import random
import time
import json

import subprocess

import numpy as np


import maxlab as mx
from bin.lib.stimulation import Stimulation

def initialize_system() -> None:
    """Initialize system into a defined state

    The function initializes the system into a defined state before
    starting any script. This way, one can be sure that the system
    is always in the same state while running the script, regardless
    of what has been done before with it. The function also powers on
    the stimulation units, which are turned off by default.

    Raises
    ------
    RuntimeError
        If system does not initialize correctly.

    """
    mx.initialize()
    if mx.send(mx.Core().enable_stimulation_power(True)) != "Ok":
        raise RuntimeError("The system didn't initialize correctly.")

def connect_stim_units_to_stim_electrodes(
    stim_electrodes: List[int], array: mx.Array
) -> List[int]:
    """Connect the stimulation units to the stimulation electrodes

    Once an array configuration has been obtained, either through routing
    or through loading a previous configuration, the stimulation units
    can be connected to the desired electrodes.

    Notes
    -----
    With this step, one needs to be careful, in rare cases it can happen
    that an electrode cannot be stimulated. For example, the electrode
    could not be routed (due to routing constraints), and the error message
    "No stimulation channel can connect to electrode: ..." will be printed.
    If this situation occurs, it is recommended to then select the electrode
    next to it.

    Parameters
    ----------
    stim_electrodes : List[int]
        List of the index of the stimulation electrodes
    array : mx.Array
        The configured array

    Returns
    -------
    List[str]
        List of stimulation units indices corresponding to the connected
        stimulation electrodes

    Raises
    ------
    RuntimeError
        If an electrode cannot be connected to a stimulation unit.
        If two electrodes are connected to the same stimulation unit.
    """
    stim_units: List[int] = []
    for stim_el in stim_electrodes:
        array.connect_electrode_to_stimulation(stim_el)
        stim = array.query_stimulation_at_electrode(stim_el)
        if len(stim) == 0:
            raise RuntimeError(
                f"No stimulation channel can connect to electrode: {str(stim_el)}"
            )
        stim_unit_int = int(stim)
        if stim_unit_int in stim_units:
            raise RuntimeError(
                f"Two electrodes connected to the same stim unit.\
                               This is not allowed. Please Select a neighboring electrode of {stim_el}!"
            )
        else:
            stim_units.append(stim_unit_int)
    return stim_units



def configure_array(electrodes: List[int], stim_electrodes: List[int]) -> mx.Array:
    """Configure array

    This function configures the array, given a list of recording
    and stimulation electrodes. An important step in this function
    is the routing, which happens once the electrodes are selected.

    Parameters
    ----------
    electrodes : List[int]
        List of the index of the recording electrodes
    stim_electrodes : List[int]
        List of the index of the stimulation electrodes

    Returns
    -------
    mx.Array
        The configured array.

    Notes
    -----
    To finalize the configuration, the array needs to be downloaded to
    the MaxOne/Two. However, before being able to do that, we first need
    to connect the stimulation units to the stimulation electrodes with the
    function `connect_stim_units_to_stim_electrodes`. This is the reason
    why `array.download` is not part of this function.

    """
    array = mx.Array("stimulation")
    array.reset()
    array.clear_selected_electrodes()
    array.select_electrodes(electrodes)
    array.select_stimulation_electrodes(stim_electrodes)
    array.route()
    return array



def powerup_stim_unit(stim_unit: int, dac_source: int) -> mx.StimulationUnit:
    """Power up and connect a stimulation unit

    This function powers up and connect a specific stimulation
    unit in the MaxOne/Two. Without it, we would not be able to
    send the prepared sequence to the device and it thus needs
    to be run before running `mx.send(stim)` (as shown in the
    function `configure_and_powerup_stim_units).

    Parameters
    ----------
    stim_unit : str
        The index of the stimulation unit to power up

    Returns
    -------
    mx.StimulationUnit
        The powered up stimulation unit

    """
    return (
        mx.StimulationUnit(stim_unit)
        .power_up(True)
        .connect(True)
        .set_voltage_mode()
        .dac_source(dac_source)
    )


def configure_and_powerup_stim_units(stim_units: List[int], dac_source: int) -> List[mx.StimulationUnit]:
    """Configure and powerup the stimulation units

    Once the electrodes are connected to the stimulation units,
    the stimulation units need to be configured and powererd up.

    Parameters
    ----------
    stim_units : List[str]
        List of stimulation units indices corresponding to the connected
        stimulation electrodes

    Returns
    -------
    List[mx.StimulationUnit]
        List of stimulation unit objects corresponding to the connected
        stimulation electrodes.

    """
    for stim_unit in stim_units:
        stim = powerup_stim_unit(stim_unit, dac_source)
        mx.send(stim)


def poweroff_all_stim_units() -> None:
    """Poweroff all stimulation units

    This function is used to make sure that every stimulation units is
    powered-off before starting sequentially to send the sequences to the
    different stimulation units individually.

    Returns
    -------
    None

    """
    for stimulation_unit in range(0, 32):
        stim = mx.StimulationUnit(stimulation_unit)
        stim.power_up(False)
        stim.connect(False)
        mx.send(stim)


if __name__ == '__main__':


    electrodes_1 = [2919, 2920, 2921, 3138, 3139, 3140, 3141, 3142, 3357, 3358, 3359, 3360, 3361, 3362, 3363, 3577, 3578, 3579, 3580, 3581, 3582, 3583, 3797, 3798, 3799, 3800, 3801, 3802, 3803, 4018, 4019, 4020, 4021, 4022, 4239, 4240, 4241]
    electrodes_2 = [4446, 4447, 4448, 4665, 4666, 4667, 4668, 4669, 4885, 4886, 4887, 4888, 4889, 5105, 5106, 5107, 5108, 5109, 5326, 5327, 5328]
    electrodes_1 = list(np.array(electrodes_1) + 80)
    electrodes = electrodes_1 + electrodes_2

    # The fist thing we do is initalize the system.
    initialize_system()

    # We have selected some recording electrodes (see at the top,
    # directly after the imports) and here we write down some
    # stimulation electrodes.
    # Note that these choices follow certain rules, i.e.
    #   * You cannot choose more than 32 stimulation electrodes.
    #   * You cannot choose more than 1024 recording electrodes.
    #   * You cannot choose two stimulation electrodes that get connected
    # to the same stimulation unit.
    # The above selected recording electrodes are just an example and
    # should showcase how one can select specific electrodes on the array.
    stim_electrodes = [3580 + 80, 4887]
    array = configure_array(electrodes, stim_electrodes)
    # If instead we use a pre-defined config, we can load it like this:
    # array = load_config("path/to/config/file.cfg")

    # Select the subset of wells we want to stimulate.
    wells = list(range(1))
    mx.activate(wells)
    stim_units = connect_stim_units_to_stim_electrodes(stim_electrodes, array)
    array.download(wells)
    mx.offset()

    mx.clear_events()  # Empty event-buffer before adding anything to it

    #poweroff_all_stim_units()

    configure_and_powerup_stim_units(stim_units[0:1], 0)
    configure_and_powerup_stim_units(stim_units[1:2], 1)

    print("Done configuration. Creating Stimulation objects")
    stim1 = Stimulation("test", 1, 
                        amplitude = 10,
                        phase = 500,
                        pulses_per_train = 8,
                        num_trains = 3,
                        pulse_interval = 300,
                        pulse_train_interval=1,
                        stim_units = None,
                        )
    
    #stim1 = Stimulation.from_frequency("test", 1, 40, 5, 10)
    

    stim2 = Stimulation("test2", 0, 
                        amplitude = 10,
                        phase = 500,
                        pulses_per_train = 12,
                        num_trains = 4,
                        pulse_interval = 200,
                        pulse_train_interval=0.8,
                        stim_units = None,
                        )

    #stim2 = Stimulation.from_frequency("test2", 0, 60, 5, 10)
    print("Done creating stimulation objects. Creating sequences")
    seq1 = stim1.create_sequence()
    seq2 = stim2.create_sequence()

    combined_sequence = Stimulation.combine_stimuli(stim2, stim1, "combined")
     
    print("Done creating sequences")
    time.sleep(5)

    print("Sending seq1")
    time.sleep(2)
    seq1.send()

    time.sleep(5)

    print("Sending seq2")
    time.sleep(2)
    seq2.send()
    
    time.sleep(5)

    print("Sending combined")
    time.sleep(2)
    combined_sequence.send()