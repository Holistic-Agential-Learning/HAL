import maxlab as mx
import random


PULSE_PER_TRAIN_LLIMIT: int = 1
PULSE_PER_TRAIN_ULIMIT: int = 200 #this is arbitrary;' but the longer, the more unreliable
STABLE_AMPLITUDE_LLIMIT: int = 0
STABLE_AMPLITUDE_ULIMIT: int = 512 #the limit is [0,1023]

#100 uS for MaxTwo and 50uS for MaxOne
STABLE_PULSEWIDTH_LLIMIT: int = 1 
STABLE_PULSEWIDTH_ULIMIT: int = 1_000
STABLE_INTER_PULSE_INTERVAL_LLIMIT: int = 10 
STABLE_INTER_PULSE_INTERVAL_ULIMIT: int = 1_000

#Note: treating each pulse as biphasic
#enter the value of amp in mV and rest in us
def macro_reward(seq_name: str, num_pulses_per_train: int = 50,
                 stable_amplitude: int = 150, stable_pulsewidth: int = 50, stable_inter_pulse_interval: int = 200):
    
    '''
    inputs:
    1) name for the sequence you are creating
    2) numbers of pulses you want per train
    4, 5, 6) (Optional) stable_amplitude, stable_pulsewidth, stable_inter_pulse_interval for the reward


    outputs:
    1) reward sequence

    '''
    dac_lsb_mV = float(mx.query_DAC_lsb_mV())
    stable_amplitude = int(stable_amplitude/dac_lsb_mV)

    assert PULSE_PER_TRAIN_LLIMIT <= num_pulses_per_train <= PULSE_PER_TRAIN_ULIMIT, (
    f"num_pulses_per_train must be between {PULSE_PER_TRAIN_LLIMIT} and {PULSE_PER_TRAIN_ULIMIT}"
    )
    assert STABLE_AMPLITUDE_LLIMIT <= stable_amplitude <= STABLE_AMPLITUDE_ULIMIT, (
        f"stable_amplitude must be between {STABLE_AMPLITUDE_LLIMIT} and {STABLE_AMPLITUDE_ULIMIT}"
    )
    assert STABLE_PULSEWIDTH_LLIMIT <= stable_pulsewidth <= STABLE_PULSEWIDTH_ULIMIT, (
        f"stable_pulsewidth must be between {STABLE_PULSEWIDTH_LLIMIT} and {STABLE_PULSEWIDTH_ULIMIT}"
    )
    assert STABLE_INTER_PULSE_INTERVAL_LLIMIT <= stable_inter_pulse_interval <= STABLE_INTER_PULSE_INTERVAL_ULIMIT, (
        f"stable_inter_pulse_interval must be between {STABLE_INTER_PULSE_INTERVAL_LLIMIT} and {STABLE_INTER_PULSE_INTERVAL_ULIMIT}"
    )

    seq = mx.Sequence(seq_name, persistent=False)
    del(seq)
    seq = mx.Sequence(seq_name, persistent=True)
    
    #cathodic biphasic
    for _ in range(num_pulses_per_train):
        seq.append(mx.DAC(0, 512 - stable_amplitude))
        seq.append(mx.DelaySamples(stable_pulsewidth))
        if stable_amplitude == 512:
         seq.append(mx.DAC(0, 512 + 511))
        else:
           seq.append(mx.DAC(0, 512 + stable_amplitude))
        seq.append(mx.DelaySamples(stable_pulsewidth))
        seq.append(mx.DAC(0, 512))
        seq.append(mx.DelaySamples(stable_inter_pulse_interval))

    return seq