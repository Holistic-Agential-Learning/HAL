#each bit is 2.9 mV
#treat time unit as 50us
from math import floor

#use this one with all the libs I have written
def mv_to_units_main(mv):
    return (floor(mv/2.9))

#this is just for test
def mv_to_units_full(mv):
    return (floor(mv/2.9) + 512)

def us_to_units(us):
    return (floor(us/50))

def sec_to_us(s):
    return (s * 1_000_000)

def us_to_s(us):
    return (us / 1_000_000)

def hz_to_period(hz):
    return(1/hz)

def period_to_hz(per):
    return (1/per)