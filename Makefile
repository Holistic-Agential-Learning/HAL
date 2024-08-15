# compiler
CXX = g++-11

# parent folder of maxlab C++ API
MAXLAB_PATH = /home/mxwbio/MaxLab/share/libmaxlab-1.0.0_45b31664d/maxlab_lib/maxlab

# include path for Maxlab and HAL C++ libraries
INCLUDE_PATH = -I$(MAXLAB_PATH)/include/maxlab -I./bin/lib/include

# maxlab lib
LIBS = -L$(MAXLAB_PATH)/lib -lmaxlab -lpthread 

# folder that will contain all executables and .o files
BUILD = ./bin/build 

# source folder for closed-loop programs
SRC = ./bin/src 

# source folder for HAL library implementations
HAL_LIB_PATH = ./bin/lib/c_src 

# all files in C++ HAL library
HAL_LIB = $(shell ls $(HAL_LIB_PATH)) 

# all files in HAL library, converted to .o
HAL_O = $(foreach cpp,$(HAL_LIB),$(HAL_LIB_PATH)/$(basename $(cpp)).o)


# add your closed-loop programs here
# 
# Note that these all have the same name as the source file, without the .cpp,
# and must be found in $(SRC)
PROGRAMS = train-wave-direction mouse_1d closed_loop_rp rp_stim_removal new-train-wave frequency-game

# create build directory, then compile all programs
all : dir $(PROGRAMS)

# creates build directory
dir:
	mkdir -p $(BUILD)

.PHONY : all

# creates .o file
%.o: %.cpp 
	$(CXX) $(INCLUDE_PATH) -c $< -o $(BUILD)/$(shell basename $@)

# compiles closed-loop program
%: $(SRC)/%.o $(HAL_O)
	$(CXX) $(foreach o,$^,$(BUILD)/$(shell basename $(o))) -o $(BUILD)/$@ $(LIBS)

clean :
	rm -r $(BUILD)