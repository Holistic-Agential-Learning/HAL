# HAL Guide
### CS Senior Capstone
\
Welcome to the team! This document will go over the basics of the HAL system, 
including an intro on the MaxWell MaxOne/Two, the MaxWell API, and the HAL repo.

The HAL software works with the MaxWell API to run closed-loop experiments that 
read, process, and react to electrophysiological data in real-time. 

## MaxWell Machines

HAL works with the MaxOne and MaxTwo, produced by [MaxWell Biosystems](https://www.mxwbio.com/), which make use of CMOS-based MEA chips to read activity from and stimulate neurons. 

Each chip (or well for the MaxTwo) has an MEA with 26400 electrodes (220 x 120). 
Up to 1020 electrodes can record data at once; these electrodes can be chosen using 
the [MaxLab Live](https://www.mxwbio.com/products/maxlab-live-software/) GUI and saved in a configuration file for reuse. Up to 30 of the recording electrodes can 
be chosen for stimulating the chip.

The MaxLab Live software can be used to pick electrodes, view neuron activity, and even send stimulations. Using the HAL system and the MaxWell API, this can all be 
done *programatically*.

There are two MaxWell machines: the [MaxOne](https://www.mxwbio.com/products/maxone-mea-system-microelectrode-array/) and the [MaxTwo](https://www.mxwbio.com/products/maxtwo-multiwell-microelectrode-array/). The MaxOne holds a single MEA and 
samples at `20,000 Hz`. The MaxTwo chips have six MEAs, and samples at a rate of `10,000 Hz` for each well. The wells are numbered 0-5 in the API, although they are 1-6
in the MaxWell Live softare. Data can be recorded from all 6 wells using MaxWell Live and the Python API, however, there is currently no support for reading in data 
from all wells at once using the closed-loop (C++) API. For now, all closed-loop, 
multi-well experiments have to be conducted *serially*. 


### API

MaxWell provides an API that works with both the MaxOne/Two, which allows 
for closed-loop experiments on neurons. The API is divided up over two languages:
Python and C++. 

The Python API is capable of running open-loop experiments on the MaxOne/Two. It can be used to automatically initialize the MaxWell system, choose recording and stimulation electrodes, build stimulations, record well data (saved as h5 files), and send stimulations. It *cannot* access chip activity in real-time. 

The C++ API is capable of running closed-loop experiments on the MaxOne/Two, meaning that it can receive chip data in real-time. The C++ API uses sockets to receive *frames* from the MaxOne/Two at each system's corresponding sample rate. 

The details of the MaxWell API are laid out in some html files created by MaxWell,
which will be provided. 

## HAL

[HAL](https://github.com/Project-Hybrot/HAL) was created to make structures for processing closed-loop data and augment the MaxWell API. 

### Repo Structure

The source for HAL is found in the `bin` folder on the repo.

### Library

### Creating Experiments

### Examples











<!---
    Written by Trevor M. Sullivan (trevor.sullivan@tufts.edu)
    September, 2024
 -->