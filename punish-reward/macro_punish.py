import maxlab as mx
import random

PULSE_PER_TRAIN_LLIMIT: int = 0
PULSE_PER_TRAIN_ULIMIT: int = 20
STABLE_AMPLITUDE_LLIMIT: int = 0
STABLE_AMPLITUDE_ULIMIT: int = 1023
STABLE_PHASE_LLIMIT: int = 2 #100 uS (i.e 50us * 2) #NOTE: TODO: make this relative to the maxone and two
STABLE_PHASE_ULIMIT: int = 20 #1000 uS (i.e 50us * 20)
STABLE_INTER_PULSE_INTERVAL_LLIMIT: int = 20 #1mS (i.e 50us * 20) #TODO: check if this can be zero
STABLE_INTER_PULSE_INTERVAL_ULIMIT: int = 2000 #100mS (i.e 50us * 2000)


def macro_punish(punish_type: str, seq_name: str, num_pulses_per_train: int,
                 stable_amplitude: int = 200, stable_phase: int = 200, stable_inter_pulse_interval: int = 200):
    '''
    inputs:
    1) type of punishment you want, currently available options: "PULSE_WIDTH", "AMPLITUDE" and "INTER_PHASE"
    2) name for the sequence you are creating
    3) numbers of pulses you want per train, prefrably even
    4, 5, 6) (Optional) stable_amplitude, stable_phase, stable_inter_pulse_interval:
        say you selected "AMPLITUDE", then what do you want the stable_phase and stable_inter_pulse_interval to be, etc.

    outputs:
    1) punishment sequence

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

    if (punish_type == "PULSE_WIDTH"):
        lowerlim = STABLE_PHASE_LLIMIT
        upperlim = STABLE_PHASE_ULIMIT

    elif (punish_type == "AMPLITUDE"):
        lowerlim = STABLE_AMPLITUDE_LLIMIT
        upperlim = STABLE_AMPLITUDE_ULIMIT

    elif (punish_type == "INTER_PHASE"):
        lowerlim =  STABLE_INTER_PULSE_INTERVAL_LLIMIT
        upperlim = STABLE_INTER_PULSE_INTERVAL_ULIMIT

    #random params generation:
    generated_values = []

    if (num_pulses_per_train % 2 != 0):
        num_pulses_per_train += 1
        print("num_pulses_per_train was not even, now num_pulses_per_train += 1! Value Changed!")
    generation_len = (num_pulses_per_train) // 2

    for _ in range(generation_len):
        rand_no = random.randint(lowerlim, upperlim)
        generated_values.append(rand_no)


    #defining our seq
    seq = mx.Sequence(seq_name, persistent=True)

    if (punish_type == "PULSE_WIDTH"):

        for i in generated_values:
            rand_no = random.randint(lowerlim, upperlim)
            generated_values.append(rand_no)

        for i in generated_values:
            seq.append(mx.DAC(0, 512 - stable_amplitude))
            seq.append(mx.DelaySamples(i))
            seq.append(mx.DAC(0, 512 + stable_amplitude))
            seq.append(mx.DelaySamples(i))
            seq.append(mx.DAC(0, 512))
            seq.append(mx.DelaySamples(stable_inter_pulse_interval))
        

    elif (punish_type == "AMPLITUDE"):

        for i in generated_values:
            generated_values.append(-1 * i)
        random.shuffle(generated_values)

        for i in generated_values:
            seq.append(mx.DAC(0, i))
            seq.append(mx.DelaySamples(stable_phase))
            seq.append(mx.DAC(0, i))
            seq.append(mx.DelaySamples(stable_phase))
            seq.append(mx.DAC(0, 512))
            seq.append(mx.DelaySamples(stable_inter_pulse_interval))
    
    elif (punish_type == "INTER_PHASE"):

        for _ in range(generation_len):
            rand_no = random.randint(lowerlim, upperlim)
            generated_values.append(rand_no)

        for i in generated_values:
            seq.append(mx.DAC(0, 512 - stable_amplitude))
            seq.append(mx.DelaySamples(stable_phase))
            seq.append(mx.DAC(0, 512 + stable_amplitude))
            seq.append(mx.DelaySamples(stable_phase))
            seq.append(mx.DAC(0, 512))
            seq.append(mx.DelaySamples(i))

    return seq