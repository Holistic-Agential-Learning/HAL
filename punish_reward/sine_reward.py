import maxlab as mx
import numpy as np
from math import floor, ceil

PULSE_PER_TRAIN_LLIMIT: int = 1
PULSE_PER_TRAIN_ULIMIT: int = 200 #this is arbitrary;' but the longer, the more unreliable
STABLE_AMPLITUDE_LLIMIT: int = 0
STABLE_AMPLITUDE_ULIMIT: int = 512 #the limit is [0,1023]

#100 uS for MaxTwo and 50uS for MaxOne
STABLE_PULSEWIDTH_LLIMIT: int = 5 
STABLE_PULSEWIDTH_ULIMIT: int = 100
STABLE_INTER_PULSE_INTERVAL_LLIMIT: int = 10 
STABLE_INTER_PULSE_INTERVAL_ULIMIT: int = 1_000

#TODO: make it frequency based later
FREQUENCY_LLIMIT = 10
FREQUENCY_ULIMIT = 1000


def sine_reward(seq_name: str, frequency: int = 100,
                stable_pulsewidth: int = 2500, stable_inter_pulse_interval: int = 10_000,
                peak_amp: int = 400, num_waves: int = 10, steps_per_wave: int = 10 ):
    
    #converting to maxOne units:
    dac_lsb_mV = float(mx.query_DAC_lsb_mV())
    peak_amp = int(peak_amp/dac_lsb_mV)
    stable_pulsewidth = floor(stable_pulsewidth/50)
    stable_inter_pulse_interval = floor(stable_inter_pulse_interval/50)

    assert STABLE_PULSEWIDTH_LLIMIT <= stable_pulsewidth <= STABLE_PULSEWIDTH_ULIMIT, (
        f"stable_pulsewidth must be between {STABLE_PULSEWIDTH_LLIMIT} and {STABLE_PULSEWIDTH_ULIMIT}"
    )
    assert STABLE_INTER_PULSE_INTERVAL_LLIMIT <= stable_inter_pulse_interval <= STABLE_INTER_PULSE_INTERVAL_ULIMIT, (
        f"stable_inter_pulse_interval must be between {STABLE_INTER_PULSE_INTERVAL_LLIMIT} and {STABLE_INTER_PULSE_INTERVAL_ULIMIT}"
    )


    #decide on the min and max amp and then increment each
    #multiple:

    

    seq = mx.Sequence(seq_name, persistent=False)
    del(seq)
    seq = mx.Sequence(seq_name, persistent=True)

    x_space = np.linspace(0, 2 * np.pi, steps_per_wave)
    y_space = np.sin(x_space) * peak_amp

    #mono sine wave
    for i in range(num_waves):
        for j in range(steps_per_wave):
            seq.append(mx.DAC(0, 512 - int(y_space[j])))
            seq.append(mx.DelaySamples(stable_pulsewidth))
            seq.append(mx.DAC(0, 512))
            seq.append(mx.DelaySamples(stable_inter_pulse_interval))

