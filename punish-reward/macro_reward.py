import maxlab as mx
import random


PULSE_PER_TRAIN_LLIMIT: int = 1
PULSE_PER_TRAIN_ULIMIT: int = 200_000 #this is arbitrary;' but the longer, the more unreliable
STABLE_AMPLITUDE_LLIMIT: int = 0
STABLE_AMPLITUDE_ULIMIT: int = 511 #the limit is [0,1023]

STABLE_PULSEWIDTH_LLIMIT: int = 1 #100 uS (i.e 100us * 1)
STABLE_PULSEWIDTH_ULIMIT: int = 10 #1000 uS (i.e 100us * 10)
STABLE_INTER_PULSE_INTERVAL_LLIMIT: int = 10 #1mS (i.e 100us * 10)
STABLE_INTER_PULSE_INTERVAL_ULIMIT: int = 1000 #100mS (i.e 100us * 1000)

#the given limits are listed below, but since they arearbitrary we'll be setting our own. 
# DEVICE = "MAXONE"
# if DEVICE == "MAXONE":
#     STABLE_PULSEWIDTH_LLIMIT: int = 2 #100 uS (i.e 50us * 2)
#     STABLE_PULSEWIDTH_ULIMIT: int = 20 #1000 uS (i.e 50us * 20)
#     STABLE_INTER_PULSE_INTERVAL_LLIMIT: int = 20 #1mS (i.e 50us * 20) #TODO: I think this limit is arbitrary, try settimg this to zero
#     STABLE_INTER_PULSE_INTERVAL_ULIMIT: int = 2000 #100mS (i.e 50us * 2000)
# elif DEVICE == "MAXTWO":
#     STABLE_PULSEWIDTH_LLIMIT: int = 1 #100 uS (i.e 100us * 1)
#     STABLE_PULSEWIDTH_ULIMIT: int = 10 #1000 uS (i.e 100us * 10)
#     STABLE_INTER_PULSE_INTERVAL_LLIMIT: int = 10 #1mS (i.e 100us * 10)
#     STABLE_INTER_PULSE_INTERVAL_ULIMIT: int = 1000 #100mS (i.e 100us * 1000)

#Note: treating each pulse as BiPhasic
def macro_reward(seq_name: str, num_pulses_per_train: int = 500,
                 stable_amplitude: int = 200, stable_pulsewidth: int = 4, stable_inter_pulse_interval: int = 200):
    
    '''
    inputs:
    1) name for the sequence you are creating
    2) numbers of pulses you want per train
    4, 5, 6) (Optional) stable_amplitude, stable_pulsewidth, stable_inter_pulse_interval for the reward


    outputs:
    1) reward sequence

    '''
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

    seq = mx.Sequence(seq_name, persistent=True)

    for _ in range(num_pulses_per_train):
        #cathodic biphasic
        seq.append(mx.DAC(0, 512 - stable_amplitude))
        seq.append(mx.DelaySamples(stable_pulsewidth))
        seq.append(mx.DAC(0, 512 + stable_amplitude))
        seq.append(mx.DelaySamples(stable_pulsewidth))
        seq.append(mx.DAC(0, 512))
        seq.append(mx.DelaySamples(stable_inter_pulse_interval))

    return seq