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


    sys.exit()
    # if len(sys.argv) > 1:
        
    #     with open(sys.argv[1]) as f:
    #         exp_params = json.load(f)
    # else:
    #     exp_params = GUI.start_gui()


    #Sys args should be: world, starting position, maybe some stimulus parameters? IDK... How do we pass in data about points of interest? A dictionary? json, like is done here? #for now, just pre-load the dictionary.
    #OR can just read data in from the json

    #Needed: a set of stimulation electrodes corresponding to "leftward" sensing
    #Stimulation electrodes for "rightward" sensing
    #Stimulation electrodes for "arrival" sensing

    # try:
    #     world = exp_params["WORLD"]
    #     location = exp_params["LOCATION"]
    #     params = ["./mouse_1d", world, location]
    # except KeyError:
    #     print("No map or location parameter in json")
    #     params = "./mouse_1d"

    params = "./mouse_1d"

    #stim_electrodes = exp_params["E_SELECTED"]
    #rec_electrodes = exp_params["E_NUMS"]
    #
    #THE BELOW ELECTRODES ARE STIMULUS INVARIANT.
    rec_electrodes = [4431,4433,4435,4437,4439,4441,4443,4445,4447,4449,4451,4453,4871,4873,4875,4877,4879,4881,4883,4885,4887,4889,4891,4893,5191,5193,5195,5197,5199,5201,5203,5205,5207,5209,5211,5213,5215,5311,5313,5315,5317,5319,5321,5323,5325,5327,5329,5331,5333,5631,5633,5635,5637,5639,5641,5643,5645,5647,5649,5651,5653,5655,5751,5753,5755,5757,5759,5761,5763,5765,5767,5769,5771,5773,6071,6073,6075,6077,6079,6081,6083,6085,6087,6089,6091,6093,6095,6191,6193,6195,6197,6199,6201,6203,6205,6207,6209,6211,6213,6511,6513,6515,6517,6519,6521,6523,6525,6527,6529,6531,6533,6535,6631,6633,6635,6637,6639,6641,6643,6645,6647,6649,6651,6653,6951,6953,6955,6957,6959,6961,6963,6965,6967,6969,6971,6973,6975,7071,7073,7075,7077,7079,7081,7083,7085,7087,7089,7091,7093,7391,7393,7395,7397,7399,7401,7403,7405,7407,7409,7411,7413,7415,7511,7513,7515,7517,7519,7521,7523,7525,7527,7529,7531,7533,7831,7833,7835,7837,7839,7841,7843,7845,7847,7849,7851,7853,7855,7951,7953,7955,7957,7959,7961,7963,7965,7967,7969,7971,7973,8271,8273,8275,8277,8279,8281,8283,8285,8287,8289,8291,8293,8295,8391,8393,8395,8397,8399,8401,8403,8405,8407,8409,8411,8413,8711,8713,8715,8717,8719,8721,8723,8725,8727,8729,8731,8733,8735,14250,14252,14254,14256,14258,14260,14262,14264,14266,14268,14270,14318,14320,14322,14324,14326,14328,14330,14332,14334,14336,14690,14692,14694,14696,14698,14700,14702,14704,14706,14708,14710,14758,14760,14762,14764,14766,14768,14770,14772,14774,14776,15130,15132,15134,15136,15138,15140,15142,15144,15146,15148,15150,15198,15200,15202,15204,15206,15208,15210,15212,15214,15216,15570,15572,15574,15576,15578,15580,15582,15584,15586,15588,15590,15638,15640,15642,15644,15646,15648,15650,15652,15654,15656,16010,16012,16014,16016,16018,16020,16022,16024,16026,16028,16030,16078,16080,16082,16084,16086,16088,16090,16092,16094,16096,16450,16452,16454,16456,16458,16460,16462,16464,16466,16468,16470,16518,16520,16522,16524,16526,16528,16530,16532,16534,16536,16890,16892,16894,16896,16898,16900,16902,16904,16906,16908,16910,16958,16960,16962,16964,16966,16968,16970,16972,16974,16976,17330,17332,17334,17336,17338,17340,17342,17344,17346,17348,17350,17398,17400,17402,17404,17406,17408,17410,17412,17414,17416,17637,17639,17641,17643,17645,17647,17649,17651,17653,17655,17657,17659,17661,17663,17665,17667,17669,17671,17673,17675,17677,17679,17681,17683,17685,17687,17689,17691,17693,17695,17697,17699,17701,17703,17705,17707,17709,17711,17713,17715,17717,17719,17721,17723,17725,17727,17729,17731,17733,17735,17737,17739,17741,17743,17745,17747,17749,17751,17753,17755,17757,17759,17761,17763,17765,17767,17769,18077,18079,18081,18083,18085,18087,18089,18091,18093,18095,18097,18099,18101,18103,18105,18107,18109,18111,18113,18115,18117,18119,18121,18123,18125,18127,18129,18131,18133,18135,18137,18139,18141,18143,18145,18147,18149,18151,18153,18155,18157,18159,18161,18163,18165,18167,18169,18171,18173,18175,18177,18179,18181,18183,18185,18187,18189,18191,18193,18195,18197,18199,18201,18203,18205,18207,18209,18517,18519,18521,18523,18525,18527,18529,18531,18533,18535,18537,18539,18541,18543,18545,18547,18549,18551,18553,18555,18557,18559,18561,18563,18565,18567,18569,18571,18573,18575,18577,18579,18581,18583,18585,18587,18589,18591,18593,18595,18597,18599,18601,18603,18605,18607,18609,18611,18613,18615,18617,18619,18621,18623,18625,18627,18629,18631,18633,18635,18637,18639,18641,18643,18645,18647,18649,18957,18959,18961,18963,18965,18967,18969,18971,18973,18975,18977,18979,18981,18983,18985,18987,18989,18991,18993,18995,18997,18999,19001,19003,19005,19007,19009,19011,19013,19015,19017,19019,19021,19023,19025,19027,19029,19031,19033,19035,19037,19039,19041,19043,19045,19047,19049,19051,19053,19055,19057,19059,19061,19063,19065,19067,19069,19071,19073,19075,19077,19079,19081,19083,19085,19087,19089,19397,19399,19401,19403,19405,19407,19409,19411,19413,19415,19417,19419,19421,19423,19425,19427,19429,19431,19433,19435,19437,19439,19441,19443,19445,19447,19449,19451,19453,19455,19457,19459,19461,19463,19465,19467,19469,19471,19473,19475,19477,19479,19481,19483,19485,19487,19489,19491,19493,19495,19497,19499,19501,19503,19505,19507,19509,19511,19513,19515,19517,19519,19521,19523,19525,19527,19529,19837,19839,19841,19843,19845,19847,19849,19851,19853,19855,19857,19859,19861,19863,19865,19867,19869,19871,19873,19875,19877,19879,19881,19883,19885,19887,19889,19891,19893,19895,19897,19899,19901,19903,19905,19907,19909,19911,19913,19915,19917,19919,19921,19923,19925,19927,19929,19931,19933,19935,19937,19939,19941,19943,19945,19947,19949,19951,19953,19955,19957,19959,19961,19963,19965,19967,19969,20277,20279,20281,20283,20285,20287,20289,20291,20293,20295,20297,20299,20301,20303,20305,20307,20309,20311,20313,20315,20317,20319,20321,20323,20325,20327,20329,20331,20333,20335,20337,20339,20341,20343,20345,20347,20349,20351,20353,20355,20357,20359,20361,20363,20365,20367,20369,20371,20373,20375,20377,20379,20381,20383,20385,20387,20389,20391,20393,20395,20397,20399,20401,20403,20405,20407,20409]
    left_stim_electrodes = [11745, 2581, 20191, 21545]
    right_stim_electrodes = [5267, 2005, 4729, 6077]
    sensory_stim_electrodes = [21073, 13607, 1703, 12227, 17875, 21445, 13885]
    stim_electrodes = left_stim_electrodes + right_stim_electrodes + sensory_stim_electrodes
    # print(exp_params)
    # converted_params = convert_parameters(exp_params)
    #Params for stimulation:
    #{'NAME': 'one_big', 'NUM_PER_TRAIN': 1, 'INTERVAL': 20, 'NUM_TRAINS': 1, 'TRAIN_INTERVAL': 400, 'PHASE': 4, 'AMPLITUDE': 200}
    #maybe add a "frequency" thing that the C++ code needs to know about? For now just hard code this...
    #need to look at how a regular stimulus was encoded


    #In the pong paper: parameters are just voltage and frequency... "phase" appears to be half of the period?

    #Each point of interest needs a characteristic stimulation pattern when actually at the location, as well as a stimulation pattern when approaching.
    points_of_interest = {
        "1": "something"
    }
    print(converted_params)

    number_pulses_per_train = converted_params["NUM_PER_TRAIN"]
    amplitude = converted_params["AMPLITUDE"]
    phase = converted_params["PHASE"]
    inter_pulse_interval = converted_params["INTERVAL"]

    mx.initialize()
    mx.send(mx.Core().enable_stimulation_power(True))

    # stimulation electrodes for configs/newconfig.cfg
    
    array = mx.Array("mouse_1d stimulation")
    array.reset()
    array.clear_selected_electrodes()
    array.select_electrodes(rec_electrodes)
    array.select_stimulation_electrodes(stim_electrodes)
    
    array.route()
    # array = config_electrodes("configs/test_config.cfg", stim_electrodes)

    wells = range(1)
    mx.activate(wells)

    # stimulation setup here 

    stimulation_units = []
    for stim_el in stim_electrodes:
        array.connect_electrode_to_stimulation(stim_el)
        stim = array.query_stimulation_at_electrode(stim_el)
        if len(stim) == 0:
            raise RuntimeError(
                f"No stimulation channel can connect to electrode: \
                    {str(stim_el)}"
            )
        stim_unit_int = int(stim)
        if stim_unit_int in stimulation_units:
            raise RuntimeError(
                f"Two electrodes connected to the same stim unit.\
                            This is not allowed. Please Select a \
                                neighboring electrode of {stim_el}!"
            )
        else:
            stimulation_units.append(stim_unit_int)


    array.download(wells)
    mx.offset()

    stimulation_unit_commands: List[mx.StimulationUnit] = []
    for stimulation_unit in stimulation_units:
        stimulation = mx.StimulationUnit(stimulation_unit).power_up(True).connect(True).set_voltage_mode().dac_source(0)
        stimulation_unit_commands.append(stimulation)
        mx.send(stimulation)

    # WHAT IS THIS???
    # s = mx.Sequence('test_seq', persistent=False)

    seq = mx.Sequence('stim_seq', persistent=True)
    stop_seq = mx.Sequence('stop_seq', persistent=True)
    stop_seq.append(mx.DelaySamples(20000))

    # conda activate jkts
    # /home/mxwbio/MaxLab/python/lib/python3.10/site-packages/maxlab

    mx.send(mx.system.GPIODirection(0b10000100))

    seq.append(mx.system.GPIOOutput(0b00000100))
    for _ in range(number_pulses_per_train):
        seq = create_stim_pulse(seq, amplitude, phase)
        seq.append(mx.DelaySamples(inter_pulse_interval))
    seq.append(mx.system.GPIOOutput(0b00000010))
    
    ############################################################################
    # WES LOOK HERE
    # change directory and file name of the recording here

    # Since the GUI makes a new experiment folder, we should probably save the data there
    # so that the params file and recording are in the same place. 
    # The date also needs to be updated in the param file to make sure it's the 
    # day the experiment was done. 

    directory_name = exp_params["FOLDER_NAME"]
    file_name = exp_params["NAME"]  # <-- THIS NEEDS TO BE CHANGED !!!!
    ############################################################################

    recording_wells = range(1)

    s = mx.Saving()
    s.open_directory(directory_name)
    s.start_file(file_name)
    s.group_delete_all()
    s.group_define(0, "all_channels", list(range(1024)))
    # s.group_define(0, "smiley", list(range(1024)))
    print("recording...")
    s.start_recording(wells)
    
    ############################################################################
    # WES LOOK HERE
    # change timing pattern here
    time.sleep(10)
    print("calling c++ script...")
    # This is the command to run (will last as long as the cpp files lasts)
    mx.send(mx.system.GPIOOutput(0b10000000))
    
    subprocess.call(params)

    mx.send(mx.system.GPIOOutput(0b10000000))
    # print("Ten minutes left")
    print("c++ script over...")
    time.sleep(10)
    ############################################################################

    s.stop_recording()
    s.stop_file()
    s.group_delete_all()
    print("finished recording")


    sys.exit()