#!/usr/bin/env python
import sys
import os
sys.path.append(os.path.dirname(__file__) + "/..")
from typing import List, Self, Optional

import maxlab as mx
from maxlab.api_object import ApiObject
import math


event_number = 100

class ArbitraryStimulation:
    def __init__(self, token: str, sequence_list: List[ApiObject]):
        self.token = token
        for command in sequence_list:
            assert isinstance(command, ApiObject)
        
        self.sequence_list = sequence_list
        self.fps = 20000
        self.duration = self.get_duration()

    def build_sequence(self, initial_delay: float = 5, persistent = True) -> mx.Sequence:
        """Creates an mx.Sequence from the sequence list.

        Args:
            initial_delay (float, optional): _description_. Defaults to 5.
            persistent (bool, optional): _description_. Defaults to True.
        """
        seq = mx.Sequence(self.token, persistent = False)
        del seq
        seq = mx.Sequence(self.token, int(initial_delay * self.fps/(10**3)), persistent)

        for command in self.sequence_list:
            if isinstance(command, ApiObject):
                seq.append(command)
        
        return seq

    def get_duration(self) -> float:
        """Returns the duration of a sequence list, in seconds.

        Args:
            sequence_list (list): List of API objects that define a sequence.

        Returns:
            float: The duration of the sequence, in frames.
        """
        duration_frames = 0
        for command in self.sequence_list:
            if type(command) == mx.DelaySamples:
                duration_frames += command.samples
        
        return duration_frames/20000 #because DelaySamples always seems to be in units of frames at 20000 fps


#TODO: Make code to convert a sequence list into something that is human readable.
#Big picture:
#Different classes inherit from Stimulation (Regular stimulation). Stimulation has a way to create more abstract stimulation sequences (eg. turning stim_units on and off in the middle).
class Stimulation(ArbitraryStimulation):
    def __init__(self, token: str, dac_source: int, amplitude: float = 100, phase: float = 500, pulses_per_train: int = 10, num_trains: int = 1, pulse_interval: float = 10, pulse_train_interval: float = 1, stim_units: Optional[List[int]] = None, maxtwo: bool = False, well: int = 0):
        """Create a Stimulation object.

        Args:
            token (str): unique identifier
            dac_source (int): The DAC channel to send signals to. Must be 0, 1, or 2.
            amplitude (float, optional): Amplitude of biphasic pulse, in mV. Suggested values between 0 and 1000. Defaults to 100.
            phase (float, optional): Stimulation pulse phase duration (half of a period), in us. Suggested values between 100 and 1000. Defaults to 500.
            pulses_per_train (int, optional): number of pulses per train. Defaults to 10.
            num_trains (int, optional): Number of pulse trains. Defaults to 1.
            pulse_interval (float, optional): Time between pulses within a single train, in ms. Suggested values between 1 and 100. Defaults to 10.
            pulse_train_interval (float, optional): Time between pulse trains, in s. Suggested values between 0.01 and 10. Defaults to 1.
            stim_units (list, optional): List of stimulation stim_units. Must have a length of less than 32. If None, just sends stimuli to the desired DAC channel. Otherwise, powering on and off stim units is included in the sequence.
                IF THIS IS USED, ENSURE THAT ALL STIM_UNITS ARE POWERED OFF TO BEGIN WITH.
            maxtwo (bool, optional): whether or not the maxtwo is being used. If True, self.fps is equal to 10000.
        """
        #Everything is converted to frames.
        self.fps = 20000
        self.dac_source = dac_source
        self.stim_units = stim_units
        self.amplitude = amplitude
        self.phase = int(phase * self.fps /(10**6))
        self.pulses_per_train = pulses_per_train
        self.num_trains = num_trains
        self.pulse_interval = int(pulse_interval * self.fps/(10**3))
        self.pulse_train_interval = int(pulse_train_interval * self.fps)
        self.well = well

        self.token = token

        super().__init__(token, self.__create_sequence_list())

        
    
    @classmethod
    def from_frequency(cls, token: str, dac_source: int, frequency: float, duration: float, amplitude: float = 100, num_trains: int = 1, pulse_train_interval: float = 1, stim_units: Optional[List[int]] = None, maxtwo: bool = False, well = 0) -> Self:
        """constructor method, using frequency and duration instead of phase and pulses per train.

        Args:
            token (str): unique identifier
            dac_source (int): The DAC channel to send signals to. Must be 0, 1, or 2 to send to a single DAC channel.
            frequency (float): Stimulation frequency, in Hz.
            duration (float): How long the stimulus should last (for a single train), in s.
            amplitude (float, optional): Amplitude of oscillation, in mV. Suggested value between 0 and 1000. Defaults to 100.
            num_trains (int, optional): Number of pulse trains. Defaults to 1.
            pulse_train_interval (float, optional): Time between pulse trains, in s. Defaults to 1.
            stim_units (list, optional): List of stimulation stim_units. Must have a length of less than 32. If None, just sends stimuli to the desired DAC channel. Otherwise, powering on and off stim units is included in the sequence.
                IF THIS IS USED, ENSURE THAT ALL STIM_UNITS ARE POWERED OFF TO BEGIN WITH.
            maxtwo (bool, optional): whether or not the maxtwo is being used. If True, self.fps is equal to 10000.


        Returns:
            Self: A Stimulation object.
        """
        phase = (5*10**5/frequency) #in microseconds. 10^6 microseconds in 1 second, divided by 2 because phase is half of a period
        pulses_per_train = duration * frequency


        return Stimulation(token, dac_source, amplitude = amplitude, phase = phase, pulses_per_train = pulses_per_train, num_trains = num_trains, pulse_interval = 0, pulse_train_interval = pulse_train_interval, stim_units = stim_units, well = well, maxtwo = maxtwo)

    


    def __create_stim_pulse(seq: mx.Sequence, amplitude: float, phase: int, dac_source: int) -> mx.Sequence:
        try:
            dac_lsb_mV = float(mx.query_DAC_lsb_mV())
        except TypeError:
            dac_lsb_mV = 1


        seq.append(mx.DAC(dac_source, 512 - int(amplitude/dac_lsb_mV)))
        seq.append(mx.DelaySamples(phase))
        seq.append(mx.DAC(dac_source, 512 + int(amplitude/dac_lsb_mV)))
        seq.append(mx.DelaySamples(phase))
        seq.append(mx.DAC(dac_source, 512))
        return seq
    
    
    def __create_sequence_list(self):
        """Create a stim sequence for the given Stimulation pattern.

        Args:
            seq (Sequence, list): an empty Sequence or list.

        Returns:
            The sequence, in whatever type seq is.
        """
        global event_number
        seq = list()

        if self.stim_units:
            #Power on appropriate stim_units.
            for stim_unit in self.stim_units:
                stim = mx.StimulationUnit(stim_unit)
                seq.append(stim.power_up(True).connect(True).set_voltage_mode().dac_source(self.dac_source))



        seq.append(mx.Event(self.well, 1, event_number, f"start_stimulation {self.token} dac {self.dac_source} amp_mV {self.amplitude} phase_us {self.phase} pulses_per_train {self.pulses_per_train} num_trains {self.num_trains} pulse_interval_ms {self.pulse_interval} pulse_train_interval_s {self.pulse_train_interval}"))
        event_number += 1
        for i in range(self.num_trains):
            for j in range(self.pulses_per_train):
                seq = Stimulation.__create_stim_pulse(seq, self.amplitude, self.phase, self.dac_source)
                seq.append(mx.DelaySamples(self.pulse_interval))
            
            seq.append(mx.DelaySamples(self.pulse_train_interval))

        seq.append(mx.Event(self.well, 1, event_number, "end_stimulation "  + self.token))
        event_number += 1

        if self.stim_units:
            #Power off appropriate stim_units.
            for stim_unit in self.stim_units:
                stim = mx.StimulationUnit(stim_unit)
                seq.append(stim.power_up(False).connect(False))
        return seq
    


    @classmethod
    def combine_stimuli(cls, stim1: Self, stim2: Self, token: str, maxtwo = False)->ArbitraryStimulation:
        """Combine two Stimulation objects into a sequence that runs them simultaneously.

        Args:
            stim1 (Self): The Stimulation object to run through dac source 0.
            stim2 (Self): The Stimulation object to run through dac source 1.
            token (str): The unique identifier token for the sequence.
            initial_delay (float, optional): The delay before the sequence, in ms. Defaults to 5.
            persistent(bool, optional): Whether or not the sequence exists on the server after its scope is complete. Defaults to True.
            maxtwo (bool, optional): whether or not the maxtwo is being used. If True, fps is equal to 10000.

        Returns:
            ArbitraryStimulation: The ArbitraryStimulation object that runs both stim1 and stim2 simultaneously.

        Notes:
            Not configured to deal with mx.DelayCycles objects.
        """         


        def process_delay_times(min_delay, max_delay, min_delay_seq):
            #Helper function
            if min_delay > 0:
                seq.append(mx.DelaySamples(min_delay))
            max_delay -= min_delay

            while(type(next_command := min_delay_seq.pop(0)) != mx.DelaySamples and (type(next_command) != mx.Event or next_command.properties[0:15] != "end_stimulation")):
                seq.append(next_command)

            if type(next_command) == mx.DelaySamples:
                min_delay = next_command.samples
            else:
                min_delay = math.inf
                seq.append(next_command)
            return min_delay, max_delay, min_delay_seq


        global event_number

        if stim1.dac_source == stim2.dac_source:
            print("WARNING: the two stimuli selected are controlled by the same DAC.")

        # assert stim1.dac_source != 0, "stim1 must have a dac source of 0."
        # assert stim2.dac_source == 1, "stim2 must have a dac source of 1."
        fps = 20000
        if maxtwo:
            fps = 10000

        seq = list()
        
        stim1_seq_list = stim1.sequence_list.copy()
        stim2_seq_list = stim2.sequence_list.copy()


        #Get through all of the setup stuff before executing delays or voltages.
        while (type(next_command_1 := stim1_seq_list.pop(0)) != mx.Event or next_command_1.properties[0:17] != "start_stimulation"):
            seq.append(next_command_1)

        while(type(next_command_2 := stim2_seq_list.pop(0)) != mx.Event or next_command_2.properties[0:17] != "start_stimulation"):
            seq.append(next_command_2)

        seq.append(mx.Event(stim1.well, 1, event_number, "start_stimulation " + token))
        seq.append(next_command_1)
        seq.append(next_command_2)
        
        event_number += 1

        #Right now, next_command_1 and next_command_2 are both either DAC or DelaySamples.
        #Step through commands 
        
        #calculate time_offset
        #if timing offset > 0, stim2 has a longer time delay.
        #if timing offset < 0, stim1 has a longer time delay.


        #right now, both are DelaySamples
        delay_time_1 = 0
        delay_time_2 = 0


        while not math.isinf(delay_time_1) or not math.isinf(delay_time_2):
            #append a delay for whichever has a lower delay.
            if delay_time_2 < delay_time_1:
                delay_time_2, delay_time_1, stim2_seq_list = process_delay_times(delay_time_2, delay_time_1, stim2_seq_list)
                
            elif delay_time_1 <= delay_time_2: #TODO: Implement DAC code 3 if delays are equal?
                delay_time_1, delay_time_2, stim1_seq_list = process_delay_times(delay_time_1, delay_time_2, stim1_seq_list)

        seq.append(mx.Event(stim1.well, 1, event_number, "end_stimulation " + token))
        event_number += 1

        for command in stim1_seq_list + stim2_seq_list:
            seq.append(command)

        return ArbitraryStimulation(token, seq)
    








if __name__ == '__main__':

    print("hello world")
    
    stim = Stimulation("test", 3)
    print(stim)
    print(stim.__dict__)
    print(dir(stim))



#maybe we rely on outside code to create the stimuli when at a given location?