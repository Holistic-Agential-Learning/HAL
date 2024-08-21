import maxlab as mx
import numpy as np
from math import floor

'''
each frame is 100 uS for MaxTwo and 50uS for MaxOne
LLIMIT = Lower limit
ULIMIT = Upper Limit
Most of these limits are somewhat arbitrary. And the Maxwell docs only talk about safe limits but not real hardware limits.
'''

PULSE_PER_TRAIN_LLIMIT: int = 1
PULSE_PER_TRAIN_ULIMIT: int = 200
STABLE_AMPLITUDE_LLIMIT: int = 0
STABLE_AMPLITUDE_ULIMIT: int = 512 #the limit is [0,1023]

STABLE_PULSEWIDTH_LLIMIT: int = 5 
STABLE_PULSEWIDTH_ULIMIT: int = 100
STABLE_INTER_PULSE_INTERVAL_LLIMIT: int = 10 
STABLE_INTER_PULSE_INTERVAL_ULIMIT: int = 1_000


#we don't want many values below 10 or above 1000, cause that can potentially skew the distribution
LAMDA_LLIMIT = 0 
LAMDA_ULIMIT = 800

#for interphase
#Note: treating each pulse as biphasic
#units in mV for Amplitude amd uS for all time related
def poission_punish(seq_name: str, num_pulses_per_train: int = 50, stable_amplitude: int = 435, stable_pulsewidth: int = 2500, lamda: int = 50):

    '''
    inputs:
    1) name for the sequence you are creating
    2) numbers of pulses you want per train
    4, 5) (Optional) stable_amplitude, stable_pulsewidth for the train
    6) The lambda for the poission distribution


    outputs:
    1) poission_punish sequence

    '''

    #converting to maxOne units:
    dac_lsb_mV = float(mx.query_DAC_lsb_mV())
    stable_amplitude = int(stable_amplitude/dac_lsb_mV)
    stable_pulsewidth = floor(stable_pulsewidth/50)
    
    #input bounds
    assert PULSE_PER_TRAIN_LLIMIT <= num_pulses_per_train <= PULSE_PER_TRAIN_ULIMIT, (
    f"num_pulses_per_train must be between {PULSE_PER_TRAIN_LLIMIT} and {PULSE_PER_TRAIN_ULIMIT}"
    )
    assert STABLE_AMPLITUDE_LLIMIT <= stable_amplitude <= STABLE_AMPLITUDE_ULIMIT, (
        f"stable_amplitude must be between {STABLE_AMPLITUDE_LLIMIT} and {STABLE_AMPLITUDE_ULIMIT}"
    )
    assert STABLE_PULSEWIDTH_LLIMIT <= stable_pulsewidth <= STABLE_PULSEWIDTH_ULIMIT, (
        f"stable_pulsewidth must be between {STABLE_PULSEWIDTH_LLIMIT} and {STABLE_PULSEWIDTH_ULIMIT}"
    )
    
    assert LAMDA_LLIMIT <= lamda <= LAMDA_ULIMIT, (
        f"lamda must be between {LAMDA_LLIMIT} and {LAMDA_ULIMIT}"
    )

    vals = np.random.poisson(lamda, num_pulses_per_train) * 1000
    vals[vals <= STABLE_INTER_PULSE_INTERVAL_LLIMIT] = STABLE_INTER_PULSE_INTERVAL_LLIMIT #replacing with the min values
    vals[vals >= STABLE_INTER_PULSE_INTERVAL_ULIMIT] = STABLE_INTER_PULSE_INTERVAL_ULIMIT #replacing with the max values

    seq = mx.Sequence(seq_name, persistent=False)
    del(seq)
    seq = mx.Sequence(seq_name, persistent=True)
    
    #biphasic pulse train generation
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