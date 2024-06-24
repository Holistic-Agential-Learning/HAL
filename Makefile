CXX = g++-11
INCLUDE_PATH = -I/home/mxwbio/MaxLab/share/libmaxlab-1.0.0_45b31664d/maxlab_lib/maxlab/include/maxlab -I./bin/lib
LIBS = -L/home/mxwbio/MaxLab/share/libmaxlab-1.0.0_45b31664d/maxlab_lib/maxlab/lib -lmaxlab -lpthread
BUILD = ./bin/build
EXAMPLE_PATH = ./examples
SRC = ./bin/src
HAL_LIB_PATH = ./bin/lib
HAL_LIB = $(HAL_LIB_PATH)/*.cpp


all : dir mouse_1d maxtwo-direction train-wave-direction

dir:
	mkdir -p $(BUILD)

.PHONY : all

%.o: %.cpp 
	$(CXX) $(INCLUDE_PATH) -c $< -o $@

train-wave-direction: $(BUILD)/train-wave-direction.o $(BUILD)/channelWindow.o $(BUILD)/electrodeMap.o
	$(CXX) $^ -o $(BUILD)/$@ $(LIBS)

# mouse_1d: mouse_1d_exp/mouse_1d.cpp mouse_1d_exp/worldstate.cpp $(HAL_LIB)
# 	$(CXX) $^ -o $(BUILD)/$@ $(INCLUDE_PATH) $(LIBS) -lpthread

# maxtwo-direction: $(SRC)/maxtwo-direction.cpp $(HAL_LIB)
# 	$(CXX) $^ -o $(BUILD)/$@ $(INCLUDE_PATH) $(LIBS) -lpthread


clean :
	rm -r $(BUILD)