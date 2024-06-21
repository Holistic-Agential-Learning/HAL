CXX = g++-11
INCLUDE_PATH = -I/home/mxwbio/MaxLab/share/libmaxlab-1.0.0_45b31664d/maxlab_lib/maxlab/include/maxlab -I./lib
LIBS = -L/home/mxwbio/MaxLab/share/libmaxlab-1.0.0_45b31664d/maxlab_lib/maxlab/lib -lmaxlab
BUILD = ./build
EXAMPLE_PATH = ./examples

all : dir mouse_1d maxtwo-direction train-wave-direction

dir:
	mkdir -p $(BUILD)

.PHONY : all

train-wave-direction: train-wave-direction.cpp lib/electrodeMap.cpp
	$(CXX) $^ -o $(BUILD)/$@ $(INCLUDE_PATH) $(LIBS) -lpthread

mouse_1d: mouse_1d_exp/mouse_1d.cpp mouse_1d_exp/worldstate.cpp
	$(CXX) $^ -o $(BUILD)/$@ $(INCLUDE_PATH) $(LIBS) -lpthread

maxtwo-direction: maxtwo-direction.cpp lib/electrodeMap.cpp
	$(CXX) $^ -o $(BUILD)/$@ $(INCLUDE_PATH) $(LIBS) -lpthread


clean :
	rm -r $(BUILD)