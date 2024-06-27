import maxlab as mx
import random

PULSE_PER_TRAIN_LLIMIT: int = 1
PULSE_PER_TRAIN_ULIMIT: int = 200_000 #this is arbitrary;' but the longer, the more unreliable
STABLE_AMPLITUDE_LLIMIT: int = 0
STABLE_AMPLITUDE_ULIMIT: int = 5 #the limit is [0,1023]


#100 uS for MaxTwo and 50uS for MaxOne
STABLE_PULSEWIDTH_LLIMIT: int = 10 #these limits matter a lot for the random num gen so set them properly
STABLE_PULSEWIDTH_ULIMIT: int = 1_000
STABLE_INTER_PULSE_INTERVAL_LLIMIT: int = 10  
STABLE_INTER_PULSE_INTERVAL_ULIMIT: int = 10_000


#Note: treating each pulse as MonoPhasic by default 
def macro_punish(punish_type: str, seq_name: str, num_pulses_per_train: int = 500,
                 stable_amplitude: int = 200, stable_pulsewidth: int = 50, stable_inter_pulse_interval: int = 200):
    '''
    inputs:
    1) type of punishment you want, currently available options: "PULSE_WIDTH", "AMPLITUDE" and "INTER_PHASE"
    2) name for the sequence you are creating
    3) (Optional) numbers of pulses you want per train, prefrably even
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
    assert STABLE_PULSEWIDTH_LLIMIT <= stable_pulsewidth <= STABLE_PULSEWIDTH_ULIMIT, (
        f"stable_pulsewidth must be between {STABLE_PULSEWIDTH_LLIMIT} and {STABLE_PULSEWIDTH_ULIMIT}"
    )
    assert STABLE_INTER_PULSE_INTERVAL_LLIMIT <= stable_inter_pulse_interval <= STABLE_INTER_PULSE_INTERVAL_ULIMIT, (
        f"stable_inter_pulse_interval must be between {STABLE_INTER_PULSE_INTERVAL_LLIMIT} and {STABLE_INTER_PULSE_INTERVAL_ULIMIT}"
    )

    if (punish_type == "PULSE_WIDTH"):
        lowerlim = STABLE_PULSEWIDTH_LLIMIT
        upperlim = STABLE_PULSEWIDTH_ULIMIT

    elif (punish_type == "AMPLITUDE"):
        lowerlim = STABLE_AMPLITUDE_LLIMIT
        upperlim = STABLE_AMPLITUDE_ULIMIT

    elif (punish_type == "INTER_PHASE"):
        lowerlim =  STABLE_INTER_PULSE_INTERVAL_LLIMIT
        upperlim = STABLE_INTER_PULSE_INTERVAL_ULIMIT

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


    if (punish_type == "AMPLITUDE"):

        new_generated_values = []
        for i in generated_values:
            new_generated_values.append(-1 * i)
        
        generated_values += new_generated_values

        random.shuffle(generated_values)

        for i in generated_values:
            seq.append(mx.DAC(0, 512 + i))
            seq.append(mx.DelaySamples(stable_pulsewidth))
            seq.append(mx.DAC(0, 512))
            seq.append(mx.DelaySamples(stable_inter_pulse_interval))



    elif (punish_type == "INTER_PHASE"):

        for _ in range(generation_len):
            rand_no = random.randint(lowerlim, upperlim)
            generated_values.append(rand_no)

        for i in generated_values:
            seq.append(mx.DAC(0, 512 - stable_amplitude))
            seq.append(mx.DelaySamples(stable_pulsewidth))
            if stable_amplitude == 512:
                seq.append(mx.DAC(0, 512 + 511))
            else:
                seq.append(mx.DAC(0, 512 + stable_amplitude))
            seq.append(mx.DelaySamples(stable_pulsewidth))
            seq.append(mx.DAC(0, 512))
            seq.append(mx.DelaySamples(i))


    elif (punish_type == "PULSE_WIDTH"):
        for _ in range(generation_len):
            rand_no = random.randint(lowerlim, upperlim)
            generated_values.append(rand_no)

        for i in generated_values:
            seq.append(mx.DAC(0, 512 - stable_amplitude))
            seq.append(mx.DelaySamples(i))
            if stable_amplitude == 512:
                seq.append(mx.DAC(0, 512 + 511))
            else:
                seq.append(mx.DAC(0, 512 + stable_amplitude))
            seq.append(mx.DelaySamples(i))
            seq.append(mx.DAC(0, 512))
            seq.append(mx.DelaySamples(stable_inter_pulse_interval))

    return seq