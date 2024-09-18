import maxlab as mx
import matplotlib.pyplot as plt

from typing import List
from time import sleep
from h5py import File
from pathlib import Path

recording_dir = str("/home/mxwbio/Desktop/HAL/data/triple_stim")
file_name = "stim"

# Parameters of the Stimulation
amplitude_A = 10  # bits
amplitude_B = 50  # bits

phase = 100  # samples -> MX1: 100/20000 = 5 ms
inter_pulse_interval = 10000  # samples -> MX1: 1000/20000 = 0.5 s


# fmt: off
electrodes = [1100, 6600, 14850]
# fmt: on


def connect_stim_units_to_stim_electrodes(
    stim_electrodes: List[int], array: mx.Array
) -> List[int]:
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
                f"Two electrodes connected to the same stim unit. This is not allowed. Please Select a neighboring electrode of {stim_el}!"
            )
        else:
            stim_units.append(stim_unit_int)
    return stim_units


if __name__ == "__main__":
    # SETUP
    mx.initialize()
    sleep(5)
    if mx.send(mx.Core().enable_stimulation_power(True)) != "Ok":
        raise RuntimeError("The system didn't initialize correctly.")
    sleep(mx.Timing.waitInit)

    wells = [0, 1, 2]

    for well in wells:

        stimulation_electrodes = [electrodes[well] + 1]
        array = mx.chip.Array("stimulation")
        array.select_electrodes(electrodes)
        array.select_stimulation_electrodes(stimulation_electrodes)
        array.route()

    
        mx.activate([well])

        stimulation_units = connect_stim_units_to_stim_electrodes(
            stimulation_electrodes, array
        )

        config = array.get_config()
        stimulation_channels = config.get_channels_for_electrodes(stimulation_electrodes)
        stimulation_channels.sort()

        mx.send(
            mx.StimulationUnit(stimulation_units[0])
            .power_up(True)
            .connect(True)
            .set_voltage_mode()
            .dac_source(0)
        )

        array.download([well])

    sleep(mx.Timing.waitAfterDownload)
    mx.offset()
    sleep(15)

    mx.clear_events()

    # START EXPERIMENT
    s = mx.Saving()
    s.open_directory(recording_dir)
    s.start_file(file_name)

    s.group_define(0, "all_channels", list(range(1024)))
    s.group_define(1, "all_channels", list(range(1024)))

    # CREATE SEQUENCE
    sequence1 = mx.Sequence("1")
    for _ in range(3):
        sequence1.append(mx.DAC(0, 512 + amplitude_A))
        sequence1.append(mx.DelaySamples(phase))
        sequence1.append(mx.DAC(0, 512))
        sequence1.append(mx.DelaySamples(inter_pulse_interval))

    sequence2 = mx.Sequence("2")
    for _ in range(5):
        sequence2.append(mx.DAC(1, 512 + amplitude_B))
        sequence2.append(mx.DelaySamples(phase))
        sequence2.append(mx.DAC(1, 512))
        sequence2.append(mx.DelaySamples(inter_pulse_interval))

    s.start_recording(wells)

    print("Start recording")
    sleep(5)  # Pre-stimulation time

    print("Sending first stimulation...")
    sequence1.send()
    sleep(5)

    print("Sending second stimulation...")
    sequence1.send()
    sleep(5)

    print("Sending third stimulation...")
    sequence1.send()
    sleep(5)

    s.stop_recording()
    sleep(mx.Timing.waitAfterRecording)
    s.stop_file()
    s.group_delete_all()

    # del sequence1
    # del sequence2

    # print(stimulation_channels)

    # VERIFY RESULTS
    # file = File(f"{recording_dir}/{file_name}.raw.h5")
    # raw_trace_A = file["wells/well000/rec0000/groups/all_channels/raw"][
    #     stimulation_channels[0], :
    # ].T
    # raw_trace_B = file["wells/well001/rec0000/groups/all_channels/raw"][
    #     stimulation_channels[1], :
    # ].T

    # plt.plot(raw_trace_A)
    # plt.plot(raw_trace_B)
    # plt.show()
