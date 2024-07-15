import maxlab as mx
import numpy as np
from math import floor


def poission_punish(seq_name: str, num_pulses_per_train: int = 50, stable_amplitude: int = 435, stable_pulsewidth: int = 2500, lamda: int = 10):
    vals = np.random.poisson(lamda, num_pulses_per_train)
    vals[vals <= 0] = 1 #replacing with the min values
    vals[vals >= 0] = 1 #replacing with the max values




    seq = mx.Sequence(seq_name, persistent=False)
    del(seq)
    seq = mx.Sequence(seq_name, persistent=True)
    
    #anodic biphasic
    for i in range(num_pulses_per_train):
        inter_pulse_interval = vals[i]
        seq.append(mx.DAC(0, 512 - stable_amplitude))
        seq.append(mx.DelaySamples(stable_pulsewidth))
        if stable_amplitude == 512:
         seq.append(mx.DAC(0, 512 + 511))
        else:
           seq.append(mx.DAC(0, 512 + stable_amplitude))
        seq.append(mx.DelaySamples(stable_pulsewidth))
        seq.append(mx.DAC(0, 512))
        seq.append(mx.DelaySamples(inter_pulse_interval))

    return seq