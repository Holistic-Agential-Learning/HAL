import maxlab as mx
import matplotlib.pyplot as plt

from typing import List
from time import sleep
from h5py import File
from pathlib import Path

from macro_reward import macro_reward
from macro_punish import macro_punish
from poission_punish import poission_punish
from sine_reward import sine_reward

recording_dir = str("/home/mxwbio/")
file_name = "stim"

# Parameters of the Stimulation
amplitude_A = 10  # bits
amplitude_B = 50  # bits

phase = 100  # samples -> MX1: 100/20000 = 5 ms
inter_pulse_interval = 10000  # samples -> MX1: 1000/20000 = 0.5 s


# fmt: off
electrodes = [4885, 4666, 4886, 4022, 5327, 5328, 5106, 5326, 3138, 3140, 2919,
              5105, 4667, 4448, 5109, 4669, 4665, 3798, 4021, 3141, 4668, 4240,
              3363, 3803, 3580, 3801, 2921, 3799, 4239, 3359, 3142, 3797, 3361,
              4020, 4241, 4018, 4889, 4447, 3357, 5108, 4888, 5107, 4446, 3583,
              3360, 3802, 3358, 3578, 2920, 4019, 3582, 3362, 3577, 4887, 3139,
              3800, 3579, 3581,]
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


if __name__ == "__main__":
    # SETUP
    filepath = Path(f"{recording_dir}/{file_name}.raw.h5")
    if filepath.is_file():
        print("save file already exists: deleting")
        filepath.unlink()

    mx.initialize()
    sleep(5)
    if mx.send(mx.Core().enable_stimulation_power(True)) != "Ok":
        raise RuntimeError("The system didn't initialize correctly.")
    sleep(mx.Timing.waitInit)

    stimulation_electrodes = [4448, 3582]
    array = mx.Array()
    array.select_electrodes(electrodes)
    array.select_stimulation_electrodes(stimulation_electrodes)
    array.route()

    wells = [0]
    mx.activate(wells)

    stimulation_units = connect_stim_units_to_stim_electrodes(
        stimulation_electrodes, array
    )

    config = array.get_config()
    stimulation_channels = config.get_channels_for_electrodes(stimulation_electrodes)
    stimulation_channels.sort()

    mx.activate([0])
    poweroff_all_stim_units()

    for stimulation_unit in stimulation_units:
        mx.send(
            mx.StimulationUnit(stimulation_unit)
            .power_up(True)
            .connect(True)
            .set_voltage_mode()
            .dac_source(0)
        )

    array.download(wells)
    sleep(mx.Timing.waitAfterDownload)
    mx.offset()
    sleep(5)

    mx.clear_events()
     
    print("starting recording")
    # START EXPERIMENT
    s = mx.Saving()
    s.open_directory(recording_dir)
    s.start_file(file_name)

    s.group_define(0, "all_channels", list(range(1024)))
    # CREATE SEQUENCE

    # myseq = macro_reward("test", 20, 100, 200, 2000)
    print("building stimulation")
    #myseq = sine_reward("sine", stable_pulsewidth=5_000, num_waves=1, stable_inter_pulse_interval=50_000, peak_amp=10, steps_per_wave=10)
    # myseq = macro_punish("PULSE_WIDTH", "test", 20, 5, 200, 2000)
    print("done building stimulation")

    s.start_recording(wells)

    print("Start stimulation")
    sleep(5)  # Pre-stimulation time
    myseq.send()

    sleep(5)  # Post-stimulation time
    print("Stop stimulation")

    s.stop_recording()
    sleep(mx.Timing.waitAfterRecording)
    s.stop_file()
    s.group_delete_all()


    print(stimulation_channels)

    # VERIFY RESULTS
    file = File(f"{recording_dir}/{file_name}.raw.h5")
    raw_trace_A = file["wells/well000/rec0000/groups/all_channels/raw"][
        stimulation_channels[0], :
    ].T

    plt.plot(raw_trace_A)
    plt.show()
