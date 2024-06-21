CXX = g++-11
INCLUDE_PATH = -I./maxlab_lib/include -I./lib
LIB_PATH = ./maxlab_lib/lib
BUILD_PATH = ./build
EXAMPLE_PATH = ./examples

all : closed-loop print-bursts stim-bursts experiment-input stim-burst-direction stim-burst-side mouse_1d
.PHONY : all

closed-loop: closed-loop.cpp
	$(CXX) $^ -o $@ -I$(INCLUDE_PATH) -L$(LIB_PATH) -lmaxlab_lib -lpthread
	
experiment-input: experiment-input.cpp
	$(CXX) $^ -o $@ -I$(INCLUDE_PATH) -L$(LIB_PATH) -lmaxlab_lib -lpthread

train-wave-direction: train-wave-direction.cpp lib/electrodeMap.cpp
	$(CXX) $^ -o $@ -I$(INCLUDE_PATH) -L$(LIB_PATH) -lmaxlab_lib -lpthread

mouse_1d: mouse_1d_exp/mouse_1d.cpp mouse_1d_exp/worldstate.cpp
	$(CXX) $^ -o $@ -I$(INCLUDE_PATH) -L$(LIB_PATH) -lmaxlab_lib -lpthread

general: general.cpp lib/electrodeMap.cpp
	$(CXX) $^ -o $@ -I$(INCLUDE_PATH) -L$(LIB_PATH) -lmaxlab_lib -lpthread

maxtwo-direction: maxtwo-direction.cpp lib/electrodeMap.cpp
	$(CXX) $^ -o $@ -I$(INCLUDE_PATH) -L$(LIB_PATH) -lmaxlab_lib -lpthread


clean :
	rm -r closed-loop print-bursts stim-bursts experiment-input stim-burst-direction stim-burst-side mouse_1d general maxtwo-direction