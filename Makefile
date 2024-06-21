# CC=g++
# LD=$(CC)
# CPPFLAGS=-g -pedantic -Wall -Wextra
# # CFLAGS=-I.
# # LDFLAGS=
# # LDLIBS=
# # INCLUDE_PATH = ./maxlab/include
# # LIB_PATH = ./maxlab/lib
# # BUILD_PATH = ./build
# # EXAMPLE_PATH = ./examples
# PROGRAM=closed-loop

# all: $(PROGRAM) 

# %.o: %.cpp
# 	$(CC) $(CPPFLAGS) $(CFLAGS) -c -o $@ $<

# $(PROGRAM): $(PROGRAM).o
# 	$(LD) $(CPPFLAGS) $(LDFLAGS) $(LDLIBS) -o $@ $<

# .PHONY:
# clean:
	# rm -f *.o $(PROGRAM)
#################################################################
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


#################################################################
# CXX = gcc-11
# CPPFLAGS =  -g -std=gnu++20 -Wpedantic -Wall -Wextra
# INCLUDE_PATH = ./maxlab_lib/maxlab/include/maxlab
# LIB_PATH = ./maxlab_lib/maxlab/lib
# BUILD_PATH = ./build
# # EXAMPLE_PATH = ./examples

# # Added by trevor and josh
# LDLIBS = -lm -lrt -lpthread #-lmaxlab

# all : closed_loop
# .PHONY : all

# %.o: %.cpp 
# 	$(CXX) -c $(CPPFLAGS) $<

# # $(LIB_PATH)/libmaxlab.a $(INCLUDE_PATH)/*.h
# closed_loop: closed-loop.o 
# 	$(CXX) $(CPPFLAGS) -o $@ $< -I$(INCLUDE_PATH) -L$(LIB_PATH)/libmaxlab.a $(LDLIBS)

# # example_filtered: $(EXAMPLE_PATH)/process_spike_events.cpp
# # 	mkdir -p $(BUILD_PATH)
# # 	$(CXX) $(CPPFLAGS) $^ -c -o $(BUILD_PATH)/$@ -I$(INCLUDE_PATH) -L$(LIB_PATH) $(LDLIBS)

# clean :
# 	rm -r *.o closed_loop


#################################################################

# CXX = gcc-11
# CPPFLAGS =  -g -std=gnu++20 -Wpedantic -Wall -Wextra
# # EXAMPLE_PATH = ./examples

# # Added by trevor and josh
# LDLIBS = -lm -lrt -lpthread #-lmaxlab

# all : test
# .PHONY : all

# %.o: %.cpp 
# 	$(CXX) -c $(CPPFLAGS) $<

# # $(LIB_PATH)/libmaxlab.a $(INCLUDE_PATH)/*.h
# test: test.o 
# 	$(CXX) $(CPPFLAGS) -o $@ $(LDLIBS) $<

# # example_filtered: $(EXAMPLE_PATH)/process_spike_events.cpp
# # 	mkdir -p $(BUILD_PATH)
# # 	$(CXX) $(CPPFLAGS) $^ -c -o $(BUILD_PATH)/$@ -I$(INCLUDE_PATH) -L$(LIB_PATH) $(LDLIBS)

# clean :
# 	rm -r *.o test

