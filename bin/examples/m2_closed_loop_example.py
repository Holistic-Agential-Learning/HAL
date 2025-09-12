'''
Caitlin testing
'''

import os, sys
import time
import subprocess

import maxlab as mx

top_level_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.append(top_level_dir)

import bin.lib.py_src.hal as hal
from bin.lib.py_src.stimulation import Stimulation

# User Input
well = 0 # list of wells between 0-5
save_dir = '/home/mxwbio/Desktop/HAL/data/CGRASS'
h5_filename = f'closed_loop_well{well}_test'
rec_elecs = [6417,6418,6419,6420,6421,6422,6423,6424,6425,6426,6427,6637,6638,6639,6640,6641,6642,6643,6644,6645,6646,6647,6857,6858,6859,6860,6861,6862,6863,6864,6865,6866,6867,7077,7078,7079,7080,7081,7082,7083,7084,7085,7086,7087,7297,7298,7299,7300,7301,7302,7303,7304,7305,7306,7307,7517,7518,7519,7520,7521,7522,7523,7524,7525,7526,7527,7737,7738,7739,7740,7741,7742,7743,7744,7745,7746,7747,7957,7958,7959,7960,7961,7962,7963,7964,7965,7966,7967,8177,8178,8179,8180,8181,8182,8183,8184,8185,8186,8187,8397,8398,8399,8400,8401,8402,8403,8404,8405,8406,8407,8617,8618,8619,8620,8621,8622,8623,8624,8625,8626,8627, 7642, 6536,6537,6538,6539,6540,6541,6542,6543,6544,6545,6546,6547,6548,6756,6757,6758,6759,6760,6761,6762,6763,6764,6765,6766,6767,6768,6976,6977,6978,6979,6980,6981,6982,6983,6984,6985,6986,6987,6988,7196,7197,7198,7199,7200,7201,7202,7203,7204,7205,7206,7207,7208,7416,7417,7418,7419,7420,7421,7422,7423,7424,7425,7426,7427,7428,7636,7637,7638,7639,7640,7641,7642,7643,7644,7645,7646,7647,7648,7856,7857,7858,7859,7860,7861,7862,7863,7864,7865,7866,7867,7868,8076,8077,8078,8079,8080,8081,8082,8083,8084,8085,8086,8087,8088,8296,8297,8298,8299,8300,8301,8302,8303,8304,8305,8306,8307,8308,8516,8517,8518,8519,8520,8521,8522,8523,8524,8525,8526,8527,8528,8736,8737,8738,8739,8740,8741,8742,8743,8744,8745,8746,8747,8748,8956,8957,8958,8959,8960,8961,8962,8963,8964,8965,8966,8967,8968,9176,9177,9178,9179,9180,9181,9182,9183,9184,9185,9186,9187,9188,9396,9397,9398,9399,9400,9401,9402,9403,9404,9405,9406,9407,9408]
stim_elecs = [7522,7642] # first electrode = trigger, second = closed-loop
            

def append_stimulation_pulse(seq: mx.Sequence, amplitude: int, event_id: int) -> mx.Sequence:
    seq.append(mx.Event(0, 1, event_id, f"event_id {event_id}"))
    seq.append(mx.DAC(0, 512 - amplitude))
    seq.append(mx.DelaySamples(4))
    seq.append(mx.DAC(0, 512 + amplitude))
    seq.append(mx.DelaySamples(4))
    seq.append(mx.DAC(0, 512))
    return seq

if __name__=='__main__':

    # Initializations from maxwell example not in HAL
    mx.send(mx.Amplifier().set_gain(512))
    # For the purpose of this example, we set the spike detection
    # threshold a bit higher, to avoid/reduce false positives.
    # Set detection threshold to 8.5x std of noise
    mx.set_event_threshold(8.5)

    s = mx.Saving() # a single h5 with multiple wells as different groups
    s.open_directory(save_dir)
    s.start_file(h5_filename)
    s.group_delete_all()

    # Well-specific initializations

    array, stimulation_units = hal.init_well(well, rec_elecs, stim_elecs, dac_source = 0, power_up=False)
    
    # Select detection electrodes to detect trigger activity - passed into C++ script
    detection_electrode = array.query_amplifier_at_electrode(stim_elecs[0] + 1)

    cmd_power_trigger_stim = mx.StimulationUnit(stimulation_units[0]).power_up(True).connect(True).set_voltage_mode().dac_source(0)
    cmd_power_down_trigger_stim = mx.StimulationUnit(stimulation_units[0]).power_up(False)
    cmd_power_cl_stim = mx.StimulationUnit(stimulation_units[1]).power_up(True).connect(True).set_voltage_mode().dac_source(0)
    cmd_power_down_cl_stim = mx.StimulationUnit(stimulation_units[1]).power_up(False)

    # Trigger pulse (simulating a spike)
    sequence1 = mx.Sequence(f'trigger', persistent=True)
    sequence1.append(cmd_power_trigger_stim)
    append_stimulation_pulse(sequence1, 6, 1)
    sequence1.append(cmd_power_down_trigger_stim)

    # Closed-loop pulse
    sequence2 = mx.Sequence(f'stimulation', persistent=True)
    sequence2.append(cmd_power_cl_stim)
    append_stimulation_pulse(sequence2, 10, 2)
    sequence2.append(cmd_power_down_cl_stim)

    s.group_define(well, f"all_channels_{well}", list(range(1024)))

    # Input for C++ script?
    print("Detection electode:", detection_electrode)

    s.start_recording([well])

    print("Start recording")

    # Deliver 200 stimulation pulses to trigger electrode in well0
    for rep in range(20):
        print(f"Sending trigger pulse for well {well}")
        sequence1.send() # send trigger sequence for well0
        time.sleep(1.5)

    # # Run c++ code here - if we do everything in c++ instead of python
    # try:
    #     subprocess.run([f"./bin/build/process_spike_events", f"{detection_electrodes[0]}"])
    # except KeyboardInterrupt:
    #     print("start-maxlab.py: ^C signalled")
    # except Exception as err:
    #     print(err)

    print("Stop recording")

    s.stop_recording()

    time.sleep(mx.Timing.waitAfterRecording)

    s.stop_file()
    s.group_delete_all()