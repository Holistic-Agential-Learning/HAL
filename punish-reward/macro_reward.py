import maxlab as mx
import random

PULSE_PER_TRAIN_LLIMIT: int = 0
PULSE_PER_TRAIN_ULIMIT: int = 20 
STABLE_AMPLITUDE_LLIMIT: int = 0
STABLE_AMPLITUDE_ULIMIT: int = 1023
STABLE_PHASE_LLIMIT: int = 2 #100 uS (i.e 50us * 2)
STABLE_PHASE_ULIMIT: int = 20 #1000 uS (i.e 50us * 20)
STABLE_INTER_PULSE_INTERVAL_LLIMIT: int = 20 #1mS (i.e 50us * 20)
STABLE_INTER_PULSE_INTERVAL_ULIMIT: int = 2000 #100mS (i.e 50us * 2000)

def macro_reward(seq_name: str, num_pulses_per_train: int,
                 stable_amplitude: int = 200, stable_phase: int = 200, stable_inter_pulse_interval: int = 200):
    
    '''
    inputs:
    1) name for the sequence you are creating
    2) numbers of pulses you want per train, prefrably even
    4, 5, 6) (Optional) stable_amplitude, stable_phase, stable_inter_pulse_interval for the reward


    outputs:
    1) reward sequence

    '''
    assert PULSE_PER_TRAIN_LLIMIT <= num_pulses_per_train <= PULSE_PER_TRAIN_ULIMIT, (
    f"num_pulses_per_train must be between {PULSE_PER_TRAIN_LLIMIT} and {PULSE_PER_TRAIN_ULIMIT}"
    )
    assert STABLE_AMPLITUDE_LLIMIT <= stable_amplitude <= STABLE_AMPLITUDE_ULIMIT, (
        f"stable_amplitude must be between {STABLE_AMPLITUDE_LLIMIT} and {STABLE_AMPLITUDE_ULIMIT}"
    )
    assert STABLE_PHASE_LLIMIT <= stable_phase <= STABLE_PHASE_ULIMIT, (
        f"stable_phase must be between {STABLE_PHASE_LLIMIT} and {STABLE_PHASE_ULIMIT}"
    )
    assert STABLE_INTER_PULSE_INTERVAL_LLIMIT <= stable_inter_pulse_interval <= STABLE_INTER_PULSE_INTERVAL_ULIMIT, (
        f"stable_inter_pulse_interval must be between {STABLE_INTER_PULSE_INTERVAL_LLIMIT} and {STABLE_INTER_PULSE_INTERVAL_ULIMIT}"
    )

    seq = mx.Sequence(seq_name, persistent=True)

    for _ in range(num_pulses_per_train):
        seq.append(mx.DAC(0, 512 - stable_amplitude))
        seq.append(mx.DelaySamples(stable_phase))
        seq.append(mx.DAC(0, 512 + stable_amplitude))
        seq.append(mx.DelaySamples(stable_phase))
        seq.append(mx.DAC(0, 512))
        seq.append(mx.DelaySamples(stable_inter_pulse_interval))

    return seq