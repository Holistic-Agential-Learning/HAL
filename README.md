# Project HAL
Holistic Agential Learning

A programming environment for creating and running closed-loop experiments on the MaxWell MaxOne and MaxTwo.

### Structure

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

Several directories (such as `src`) contain an `archive` subdirectory. This 
contains old experiments or test scripts that are *not* guaranteed to be 
compatible with the current state of HAL.  

Work-in-progress documentation: [https://project-hal.github.io/](https://project-hal.github.io/)

Wesley Clawson, Trevor Sullivan, Nathan Wu, and Viraj Cz
2024
