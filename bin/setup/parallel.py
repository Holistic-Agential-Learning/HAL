#!/usr/bin/env python
from typing import List

import random
import time
import bin.gui.GUI as GUI
import json
import sys
import subprocess
import os



import maxlab as mx

from bin.lib.stimulation import Stimulation

############################################################################
# INSTRUCTIONS FOR WES
#
#   The next two lines of code are the stimulation electrodes and the 
# recording channel config. Change these whenever you load in a new neuron
# culture

# stim_electrodes = [3401, 8683, 14833, 22325]
rec_electrodes = []

# start by running this program with 
#       
#       ./start-maxlab.py examples/one_big.json
#
# You can modify one_big.json to change the stimulation
# 
# When this program prints "start C++ file now", run the following command in 
# another terminal
#
#       ./stim-burst-side
#
# If you want to change the sleeping patterns or where the recording file is 
# saved, scroll to the bottom part of this file and follow the instructions
# there.
############################################################################

# for timing, multiply by 20000 to get # of frames
# for delaySamples, divide by 50 to get # of frames
# rec_electrodes = [4431,4433,4435,4437,4439,4441,4443,4445,4447,4449,4451,4453,4871,4873,4875,4877,4879,4881,4883,4885,4887,4889,4891,4893,5191,5193,5195,5197,5199,5201,5203,5205,5207,5209,5211,5213,5215,5311,5313,5315,5317,5319,5321,5323,5325,5327,5329,5331,5333,5631,5633,5635,5637,5639,5641,5643,5645,5647,5649,5651,5653,5655,5751,5753,5755,5757,5759,5761,5763,5765,5767,5769,5771,5773,6071,6073,6075,6077,6079,6081,6083,6085,6087,6089,6091,6093,6095,6191,6193,6195,6197,6199,6201,6203,6205,6207,6209,6211,6213,6511,6513,6515,6517,6519,6521,6523,6525,6527,6529,6531,6533,6535,6631,6633,6635,6637,6639,6641,6643,6645,6647,6649,6651,6653,6951,6953,6955,6957,6959,6961,6963,6965,6967,6969,6971,6973,6975,7071,7073,7075,7077,7079,7081,7083,7085,7087,7089,7091,7093,7391,7393,7395,7397,7399,7401,7403,7405,7407,7409,7411,7413,7415,7511,7513,7515,7517,7519,7521,7523,7525,7527,7529,7531,7533,7831,7833,7835,7837,7839,7841,7843,7845,7847,7849,7851,7853,7855,7951,7953,7955,7957,7959,7961,7963,7965,7967,7969,7971,7973,8271,8273,8275,8277,8279,8281,8283,8285,8287,8289,8291,8293,8295,8391,8393,8395,8397,8399,8401,8403,8405,8407,8409,8411,8413,8711,8713,8715,8717,8719,8721,8723,8725,8727,8729,8731,8733,8735,14250,14252,14254,14256,14258,14260,14262,14264,14266,14268,14270,14318,14320,14322,14324,14326,14328,14330,14332,14334,14336,14690,14692,14694,14696,14698,14700,14702,14704,14706,14708,14710,14758,14760,14762,14764,14766,14768,14770,14772,14774,14776,15130,15132,15134,15136,15138,15140,15142,15144,15146,15148,15150,15198,15200,15202,15204,15206,15208,15210,15212,15214,15216,15570,15572,15574,15576,15578,15580,15582,15584,15586,15588,15590,15638,15640,15642,15644,15646,15648,15650,15652,15654,15656,16010,16012,16014,16016,16018,16020,16022,16024,16026,16028,16030,16078,16080,16082,16084,16086,16088,16090,16092,16094,16096,16450,16452,16454,16456,16458,16460,16462,16464,16466,16468,16470,16518,16520,16522,16524,16526,16528,16530,16532,16534,16536,16890,16892,16894,16896,16898,16900,16902,16904,16906,16908,16910,16958,16960,16962,16964,16966,16968,16970,16972,16974,16976,17330,17332,17334,17336,17338,17340,17342,17344,17346,17348,17350,17398,17400,17402,17404,17406,17408,17410,17412,17414,17416,17637,17639,17641,17643,17645,17647,17649,17651,17653,17655,17657,17659,17661,17663,17665,17667,17669,17671,17673,17675,17677,17679,17681,17683,17685,17687,17689,17691,17693,17695,17697,17699,17701,17703,17705,17707,17709,17711,17713,17715,17717,17719,17721,17723,17725,17727,17729,17731,17733,17735,17737,17739,17741,17743,17745,17747,17749,17751,17753,17755,17757,17759,17761,17763,17765,17767,17769,18077,18079,18081,18083,18085,18087,18089,18091,18093,18095,18097,18099,18101,18103,18105,18107,18109,18111,18113,18115,18117,18119,18121,18123,18125,18127,18129,18131,18133,18135,18137,18139,18141,18143,18145,18147,18149,18151,18153,18155,18157,18159,18161,18163,18165,18167,18169,18171,18173,18175,18177,18179,18181,18183,18185,18187,18189,18191,18193,18195,18197,18199,18201,18203,18205,18207,18209,18517,18519,18521,18523,18525,18527,18529,18531,18533,18535,18537,18539,18541,18543,18545,18547,18549,18551,18553,18555,18557,18559,18561,18563,18565,18567,18569,18571,18573,18575,18577,18579,18581,18583,18585,18587,18589,18591,18593,18595,18597,18599,18601,18603,18605,18607,18609,18611,18613,18615,18617,18619,18621,18623,18625,18627,18629,18631,18633,18635,18637,18639,18641,18643,18645,18647,18649,18957,18959,18961,18963,18965,18967,18969,18971,18973,18975,18977,18979,18981,18983,18985,18987,18989,18991,18993,18995,18997,18999,19001,19003,19005,19007,19009,19011,19013,19015,19017,19019,19021,19023,19025,19027,19029,19031,19033,19035,19037,19039,19041,19043,19045,19047,19049,19051,19053,19055,19057,19059,19061,19063,19065,19067,19069,19071,19073,19075,19077,19079,19081,19083,19085,19087,19089,19397,19399,19401,19403,19405,19407,19409,19411,19413,19415,19417,19419,19421,19423,19425,19427,19429,19431,19433,19435,19437,19439,19441,19443,19445,19447,19449,19451,19453,19455,19457,19459,19461,19463,19465,19467,19469,19471,19473,19475,19477,19479,19481,19483,19485,19487,19489,19491,19493,19495,19497,19499,19501,19503,19505,19507,19509,19511,19513,19515,19517,19519,19521,19523,19525,19527,19529,19837,19839,19841,19843,19845,19847,19849,19851,19853,19855,19857,19859,19861,19863,19865,19867,19869,19871,19873,19875,19877,19879,19881,19883,19885,19887,19889,19891,19893,19895,19897,19899,19901,19903,19905,19907,19909,19911,19913,19915,19917,19919,19921,19923,19925,19927,19929,19931,19933,19935,19937,19939,19941,19943,19945,19947,19949,19951,19953,19955,19957,19959,19961,19963,19965,19967,19969,20277,20279,20281,20283,20285,20287,20289,20291,20293,20295,20297,20299,20301,20303,20305,20307,20309,20311,20313,20315,20317,20319,20321,20323,20325,20327,20329,20331,20333,20335,20337,20339,20341,20343,20345,20347,20349,20351,20353,20355,20357,20359,20361,20363,20365,20367,20369,20371,20373,20375,20377,20379,20381,20383,20385,20387,20389,20391,20393,20395,20397,20399,20401,20403,20405,20407,20409]
# stim_electrodes = [11745, 2581, 20191, 21545, 5267, 2005, 4729, 6077]
# stim_electrodes = [21073, 13607, 1703, 12227, 17875, 21445, 13885] for configs/3_27_24


# load recording electrodes and stimulation electrodes
def config_electrodes(electrode_config, stim_electrodes):
    
    # recording electrodes config file
    array = mx.Array("stimulation")
    array.load_config(electrode_config)

    array.reset()
    # array.clear_selected_electrodes()
    # array.select_electrodes()
    array.select_stimulation_electrodes(stim_electrodes)
    array.route()

    return array

# create stimulation pulse (from maxlab tutorial page)
def create_stim_pulse(seq: mx.Sequence, amplitude: int, phase: int) -> mx.Sequence:
    seq.append(mx.DAC(0, 512 - amplitude))
    seq.append(mx.DelaySamples(phase))
    seq.append(mx.DAC(0, 512 + amplitude))
    seq.append(mx.DelaySamples(phase))
    seq.append(mx.DAC(0, 512))
    return seq

if __name__ == '__main__':
    print("running start-maxlab...")

    configs = ["", "", "", "", "", ""]

    if len(sys.argv) > 1:
        f = open(sys.argv[1], "r")
        exp_params = json.load(f)
        f.close()
    else:
        f = open(GUI.start_gui(), "r")
        exp_params = json.load(f)
        f.close()

    program_file = open("./bin/gui/programs.json", "r")
    # program_parameters = json.load(program_file)[exp_params["-PROGRAM-"]]["parameters"]
        
    if exp_params['-MAXTWO-']:
        wells = exp_params['WELLS']
    else:
        wells = [0]
    
    for well in wells:
        mx.activate([well])
        mx.set_primary_well(well)

        # stim_electrodes = exp_params["E_SELECTED"]
        rec_electrodes = exp_params["CONFIGS"][str(well)]["E_NUMS"]
        
        does_stimulations = False
        # if exp_params["STIMULATIONS"] == {}:
        #     does_stimulations = False

        mx.initialize()
        mx.send(mx.Core().enable_stimulation_power(True))

        # stimulation electrodes for configs/newconfig.cfg
        
        array = mx.Array("stimulation")
        array.reset()
        array.clear_selected_electrodes()
        #NOTE: stim_electrodes can include electrodes that aren't in rec_electrodes. In the future, maybe throw a warning if this is the case
        if not does_stimulations:
            print("not doing stimulations")
            stim_electrodes = []
        array.select_electrodes(stim_electrodes + rec_electrodes)
        if does_stimulations:
            array.select_stimulation_electrodes(stim_electrodes)
        
        array.route()

        # stimulation setup here 
        if does_stimulations:
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

            stimulation_unit_commands: List[mx.StimulationUnit] = []
            for stimulation_unit in stimulation_units:
                stimulation = mx.StimulationUnit(stimulation_unit).power_up(True).connect(True).set_voltage_mode().dac_source(0)
                stimulation_unit_commands.append(stimulation)
                mx.send(stimulation)

        directory_name = exp_params["FOLDER"]
        file_name = exp_params["NAME"] 
        config_file_name = directory_name + "/" + file_name + f"_well_{well}_config.cfg"

        print(config_file_name)
        #save the config prior to running the code
        array.save_config(config_file_name)
        
        configs[well] = config_file_name

        array.download([well])

        # end of loop

    mx.offset()

    mx.clear_events() 

    if does_stimulations:
        stimulations = exp_params['STIMULATIONS']
        for stim_name in stimulations.keys():
            stim = Stimulation(stim_name, 0, 
                amplitude = float(stimulations[stim_name]["AMPLITUDE"]), 
                phase = float(stimulations[stim_name]["PHASE"]), 
                pulses_per_train = int(stimulations[stim_name]["NUM_PER_TRAIN"]),
                num_trains = int(stimulations[stim_name]["NUM_TRAINS"]),
                pulse_interval = float(stimulations[stim_name]["INTERVAL"]),
                pulse_train_interval = float(stimulations[stim_name]["TRAIN_INTERVAL"]),
                maxtwo = exp_params['-MAXTWO-'],
                well = well, 
            )

            seq = stim.create_sequence(persistent = True)

    #Create start train and end sequences. TODO: LOOP THROUGH ALL WELLS AND DO THIS
    start_seq = mx.Sequence("before-training", persistent = False)
    del start_seq
    start_seq = mx.Sequence("before-training", persistent = True)
    start_seq.append(mx.Event(well, 1, 2, "before_training 1"))

    train_seq = mx.Sequence("training", persistent = False)
    del train_seq
    train_seq = mx.Sequence("training", persistent = True)
    train_seq.append(mx.Event(well, 1, 3, "training 1"))

    end_seq = mx.Sequence("after-training", persistent = False)
    del end_seq
    end_seq = mx.Sequence("after-training", persistent = True)
    end_seq.append(mx.Event(well, 1, 4, "after_training 1"))

    program_args = [f"./bin/build/raw-data-test"]

    if exp_params['-MAXTWO-']:
        program_args.append("--maxtwo")

    # for name in program_parameters.keys():
    #     if exp_params[name] != "":
    #         program_args.append(program_parameters[name]["arg"])
    #         program_args.append(exp_params[name])
    
    for well in wells:
        program_args.append(f"--config{well}")
        program_args.append(configs[well])

    mx.activate(wells)

    s = mx.Saving()
    s.open_directory(directory_name)
    s.start_file(file_name)
    s.group_delete_all()
    
    for well in wells:
        s.group_define(well, f"all_channels_{well}", list(range(1024)))

    # s.group_define(0, "smiley", list(range(1024)))
    print("recording...")
    s.start_recording(wells)

    print("calling c++ script...")

    # This is the command to run (will last as long as the cpp files lasts)
    try:
        subprocess.run(program_args)
    except KeyboardInterrupt:
        print("start-maxlab.py: ^C signalled")
    except Exception as err:
        print(err)

    print("c++ script over...")

    s.stop_recording()
    s.stop_file()
    s.group_delete_all()
    print("finished recording")
