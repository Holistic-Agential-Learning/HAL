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

The source for HAL is found in the `bin` folder on the repo. There are 3 main folders within `bin`:

* `build` : contains all executables and object files for closed-loop experiments. 
This folder is automatically created/destroyed by the `Makefile`, located in the 
top-level directory.
* `lib` : contains the HAL library modules
  * `py_src` : source code for Python modules
  * `include` : header files for C++ modules
  * `c_src` : source code for C++ modules
* `setup` : Python scripts for setting up experiments. These initialize the well(s), 
configure electrodes, create stimulations, and often run a closed-loop program. There are a couple of open-loop experiments here.
* `src` : C++ source code for closed-loop experiments


### Library

The documentation for the HAL library is in the source code (found in `bin/lib`), 
but also on our [website](https://project-hybrot.github.io/overview.html). This 
site is still under construction, but almost all of the function contracts are there, nicely formatted, with a few visuals and examples.

### Examples

Here are some files to look at for examples of how we create experiments with 
HAl and the MaxWell API:

* `bin/examples/m2_open_loop_example.py` : an example open-loop script that showcases
the MaxWell API and HAL
* `bin/setup/button_detection.py` : a setup script for testing the logic of 
button presses for the `NES` class. It sets up some stimulations for testing on 
a blank chip and creates events, which can be used as markers in the final `h5` 
file output.
* `bin/src/button-detection.cpp` : a closed-loop experiment used to test the 
`NES` class, called by `button_detection.py`. Showcases the `NES` class.
* `bin/src/new-train-wave.cpp` : a closed-loop experiment that trains the neurons
to burst in a specific direction by sending different stimulations based on 
the burst direction. Showcases the `WaveDetector` class.


#
For any questions, feel free to reach out to Wes or Trevor:

Wesley Clawson, wesley.clawson@tufts.edu\
Trevor Sullivan, trevor.sullivan@tufts.edu






<!---
    Written by Trevor M. Sullivan (trevor.sullivan@tufts.edu)
    September, 2024
 -->