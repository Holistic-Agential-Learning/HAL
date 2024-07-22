from typing import List
import random
import time
import maxlab as mx
mx.initialize()
mx.send(mx.Core().enable_stimulation_power(True))

#TODO: Ask Nathan how to Load config here instead
electrodes = [4885, 4666, 4886, 4022, 5327, 5328, 5106, 5326, 3138, 3140, 3580, 4887]
stim_electrodes = [3580, 4887]
# array = mx.Array("stimulation")
# array.load_config("path/to/config/file.cfg")

array = mx.Array("stimulation")
array.reset()
array.clear_selected_electrodes()
array.select_electrodes(electrodes)
array.select_stimulation_electrodes(stim_electrodes)
array.route()

wells = list(range(1)) #this shall activate zero?
mx.activate(wells)

stimulation_units = []

#check the following code
for stimulation_electrode in stim_electrodes:
    array.connect_electrode_to_stimulation(stimulation_electrode)
    stim = array.query_stimulation_at_electrode(stimulation_electrode)
    if len(stim) == 0:
        raise RuntimeError(
            f"No stimulation channel can connect to electrode: {str(stimulation_electrode)}"
        )
    stim_unit_int = int(stim)
    if stim_unit_int in stimulation_units:
        raise RuntimeError(
            f"Two electrodes connected to the same stim unit.\
                           This is not allowed. Please Select a neighboring electrode of {stimulation_electrode}!"
        )
    else:
        stimulation_units.append(stim_unit_int)

array.download(wells)
mx.offset()

stimulation_unit_commands: List[mx.StimulationUnits] = []
for stimulation_unit in stimulation_units:
    stimulation = mx.StimulationUnit(stimulation_unit).power_up(True).connect(True).set_voltage_mode().dac_source(0)
    stimulation_unit_commands.append(stimulation)
    mx.send(stimulation)

#replace this with a real one
def create_stim_pulse(seq: mx.Sequence, amplitude: int, phase: int) -> mx.Sequence:
    seq.append(mx.DAC(0, 512 - amplitude))
    seq.append(mx.DelaySamples(phase))
    seq.append(mx.DAC(0, 512 + amplitude))
    seq.append(mx.DelaySamples(phase))
    seq.append(mx.DAC(0, 512))
    return seq

number_pulses_per_train = 10
amplitude = 200
phase = 200
inter_pulse_interval = 200
seq = mx.Sequence()

for _ in range(number_pulses_per_train):
    seq = create_stim_pulse(seq, amplitude, phase)
    seq.append(mx.DelaySamples(inter_pulse_interval))

directory_name = "\tmp"
file_name = "stim"
recording_wells = [0]

s = mx.Saving()
s.open_directory(directory_name)
s.start_file(file_name)
s.group_delete_all()

s.group_define(0, "all_channels", list(range(1024)))
s.start_recording(recording_wells)
number_pulse_trains = 5

for _ in range(number_pulse_trains):
    print("Send pulse")
    seq.send()
    time.sleep(10)

s.stop_recording()
s.stop_file()
s.group_delete_all()