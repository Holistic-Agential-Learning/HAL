import maxlab as mx
import numpy as np
from math import floor, ceil

PULSE_PER_TRAIN_LLIMIT: int = 1
PULSE_PER_TRAIN_ULIMIT: int = 200 #this is arbitrary;' but the longer, the more unreliable
STABLE_AMPLITUDE_LLIMIT: int = 0
STABLE_AMPLITUDE_ULIMIT: int = 512 #the limit is [0,1023]

#100 uS for MaxTwo and 50uS for MaxOne
STABLE_PULSEWIDTH_LLIMIT: int = 1 
STABLE_PULSEWIDTH_ULIMIT: int = 1_000
STABLE_INTER_PULSE_INTERVAL_LLIMIT: int = 10 
STABLE_INTER_PULSE_INTERVAL_ULIMIT: int = 1_000

FREQUENCY_LLIMIT = 10
FREQUENCY_ULIMIT = 1000


def sine_reward(seq_name: str, num_pulses_per_train: int = 50, frequency: int = 100,
                stable_pulsewidth: int = 2500, stable_inter_pulse_interval: int = 10_000,
                init_amp: int = 100, peak_amp: int = 400, total_steps: int = 10 ):
     #converting to maxOne units:
    dac_lsb_mV = float(mx.query_DAC_lsb_mV())
#    stable_amplitude = int(stable_amplitude/dac_lsb_mV)
    stable_pulsewidth = floor(stable_pulsewidth/50)
    stable_inter_pulse_interval = floor(stable_inter_pulse_interval/50)

    assert PULSE_PER_TRAIN_LLIMIT <= num_pulses_per_train <= PULSE_PER_TRAIN_ULIMIT, (
    f"num_pulses_per_train must be between {PULSE_PER_TRAIN_LLIMIT} and {PULSE_PER_TRAIN_ULIMIT}"
    )
    # assert STABLE_AMPLITUDE_LLIMIT <= stable_amplitude <= STABLE_AMPLITUDE_ULIMIT, (
    #     f"stable_amplitude must be between {STABLE_AMPLITUDE_LLIMIT} and {STABLE_AMPLITUDE_ULIMIT}"
    # )
    assert STABLE_PULSEWIDTH_LLIMIT <= stable_pulsewidth <= STABLE_PULSEWIDTH_ULIMIT, (
        f"stable_pulsewidth must be between {STABLE_PULSEWIDTH_LLIMIT} and {STABLE_PULSEWIDTH_ULIMIT}"
    )
    assert STABLE_INTER_PULSE_INTERVAL_LLIMIT <= stable_inter_pulse_interval <= STABLE_INTER_PULSE_INTERVAL_ULIMIT, (
        f"stable_inter_pulse_interval must be between {STABLE_INTER_PULSE_INTERVAL_LLIMIT} and {STABLE_INTER_PULSE_INTERVAL_ULIMIT}"
    )


    #decide on the min and max amp and then increment each
    #multiple:

    multiplier = ceil(num_pulses_per_train / total_steps)
    seq = mx.Sequence(seq_name, persistent=False)
    del(seq)
    seq = mx.Sequence(seq_name, persistent=True)

    amplitude_arr = np.linspace(init_amp, peak_amp, total_steps)
    amplitude_arr = amplitude_arr * multiplier

        #anodic biphasic
    for i in range(num_pulses_per_train):
        seq.append(mx.DAC(0, 512 - int(amplitude_arr[i])))
        seq.append(mx.DelaySamples(stable_pulsewidth))
        if int(amplitude_arr[i]) == 512:
         seq.append(mx.DAC(0, 512 + 511))
        else:
           seq.append(mx.DAC(0, 512 + int(amplitude_arr[i])))
        seq.append(mx.DelaySamples(stable_pulsewidth))
        seq.append(mx.DAC(0, 512))
        seq.append(mx.DelaySamples(stable_inter_pulse_interval))

