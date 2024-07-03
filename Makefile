CXX = g++-11

MAXLAB_PATH = /home/mxwbio/MaxLab/share/libmaxlab-1.0.0_45b31664d/maxlab_lib/maxlab

INCLUDE_PATH = -I$(MAXLAB_PATH)/include/maxlab -I./bin/lib/include
LIBS = -L$(MAXLAB_PATH)/lib -lmaxlab -lpthread
BUILD = ./bin/build
EXAMPLE_PATH = ./examples
SRC = ./bin/src

# HAL Library Variables
HAL_LIB_PATH = ./bin/lib/c_src
HAL_LIB = $(shell ls $(HAL_LIB_PATH))

# all .o files in hal lib
HAL_O = $(foreach cpp,$(HAL_LIB),$(HAL_LIB_PATH)/$(basename $(cpp)).o)

PROGRAMS = train-wave-direction mouse_1d raw-data-test reward-punish

all : dir $(PROGRAMS)

dir:
	mkdir -p $(BUILD)

.PHONY : all

%.o: %.cpp 
	$(CXX) $(INCLUDE_PATH) -c $< -o $(BUILD)/$(shell basename $@)

train-wave-direction: $(SRC)/train-wave-direction.o $(HAL_O)
	$(CXX) $(foreach o,$^,$(BUILD)/$(shell basename $(o))) -o $(BUILD)/$@ $(LIBS)

raw-data-test: $(SRC)/raw-data-test.o $(HAL_O)
	$(CXX) $(foreach o,$^,$(BUILD)/$(shell basename $(o))) -o $(BUILD)/$@ $(LIBS)

mouse_1d: $(SRC)/mouse_1d.o $(HAL_O)
	$(CXX) $(foreach o,$^,$(BUILD)/$(shell basename $(o))) -o $(BUILD)/$@ $(LIBS)

reward-punish: $(SRC)/closed_loop_rp.o $(HAL_O)
	$(CXX) $(foreach o,$^,$(BUILD)/$(shell basename $(o))) -o $(BUILD)/$@ $(LIBS)

clean :
	rm -r $(BUILD)