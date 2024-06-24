CXX = g++-11
INCLUDE_PATH = -I/home/mxwbio/MaxLab/share/libmaxlab-1.0.0_45b31664d/maxlab_lib/maxlab/include/maxlab -I./bin/lib
LIBS = -L/home/mxwbio/MaxLab/share/libmaxlab-1.0.0_45b31664d/maxlab_lib/maxlab/lib -lmaxlab -lpthread
BUILD = ./bin/build
EXAMPLE_PATH = ./examples
SRC = ./bin/src
HAL_LIB_PATH = ./bin/lib
HAL_LIB = $(HAL_LIB_PATH)/*.cpp


all : dir train-wave-direction mouse_1d maxtwo-direction

dir:
	mkdir -p $(BUILD)

.PHONY : all

%.o: %.cpp 
	$(CXX) $(INCLUDE_PATH) -c $< -o $(BUILD)/$(shell basename $@)

train-wave-direction: $(SRC)/train-wave-direction.o $(HAL_LIB_PATH)/channelWindow.o  $(HAL_LIB_PATH)/electrodeMap.o
	$(CXX) $(foreach o,$^,$(BUILD)/$(shell basename $(o))) -o $(BUILD)/$@ $(LIBS)

mouse_1d: mouse_1d_exp/mouse_1d.o mouse_1d_exp/worldstate.o $(HAL_LIB_PATH)/channelWindow.o $(HAL_LIB_PATH)/electrodeMap.o
	$(CXX) $(foreach o,$^,$(BUILD)/$(shell basename $(o))) -o $(BUILD)/$@ $(LIBS)

maxtwo-direction: $(SRC)/maxtwo-direction.o $(HAL_LIB_PATH)/channelWindow.o  $(HAL_LIB_PATH)/electrodeMap.o
	$(CXX) $(foreach o,$^,$(BUILD)/$(shell basename $(o))) -o $(BUILD)/$@ $(LIBS)


# train-wave-direction: $(SRC)/train-wave-direction.cpp $(HAL_LIB)
# 	$(CXX) $^ -o $(BUILD)/$@ $(INCLUDE_PATH) $(LIBS) -lpthread


# mouse_1d: mouse_1d_exp/mouse_1d.cpp mouse_1d_exp/worldstate.cpp $(HAL_LIB)
# 	$(CXX) $^ -o $(BUILD)/$@ $(INCLUDE_PATH) $(LIBS) -lpthread

# maxtwo-direction: $(SRC)/maxtwo-direction.cpp $(HAL_LIB)
# 	$(CXX) $^ -o $(BUILD)/$@ $(INCLUDE_PATH) $(LIBS) -lpthread


clean :
	rm -r $(BUILD)