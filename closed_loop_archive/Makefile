CXX = g++-11
INCLUDE_PATH = -I../maxlab_lib/include -I../lib
LIB_PATH = ../maxlab_lib/lib
BUILD_PATH = ../build
EXAMPLE_PATH = ../examples

all : print-bursts print-bursts-old stim-bursts tim-burst-direction 

print-bursts: print-bursts.cpp
	$(CXX) $^ -o $@ -I$(INCLUDE_PATH) -L$(LIB_PATH) -lmaxlab_lib -lpthread

print-bursts-old: print-bursts.cpp
	$(CXX) $^ -o $@ -I$(INCLUDE_PATH) -L$(LIB_PATH) -lmaxlab_lib -lpthread

stim-bursts: stim-bursts.cpp
	$(CXX) $^ -o $@ -I$(INCLUDE_PATH) -L$(LIB_PATH) -lmaxlab_lib -lpthread

stim-burst-direction: stim-burst-direction.cpp
	$(CXX) $^ -o $@ -I$(INCLUDE_PATH) -L$(LIB_PATH) -lmaxlab_lib -lpthread

clean :
	rm -r print-bursts print-bursts-old stim-bursts tim-burst-direction 
