#include <zmp.hpp>
#include <stdlib.h>
#include <stdio.h>
#include <iostream>
#include <unistd.h>
#include <signal.h>
#include <vector>
#include <unistd.h>
#include <fstream>
#include <assert.h>
#include <limits.h>
#include <random>
#include <string>
#include "hal.h"
#include <map>
#include <algorithm>

using namespace std;

int main(int argc, char * argv[]) {
    zmq::context_t context{1};

    zmq::socket_t sock{context, zmq::socket_type::rep};
    sock.bind("tcp://*:5555");

    for (int i = 0; i < 10; i++) {
        string msg = to_string(i);
        sock.send(zmq::buffer(msg), zmq::send_flags::none);
    }

    string msg = "stop";
    sock.send(zmq::buffer(msg), zmq::send_flags::none);
}