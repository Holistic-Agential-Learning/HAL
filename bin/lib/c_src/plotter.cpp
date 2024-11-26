/**
 * @file plotter.cpp
 * @author Trevor Sullivan (trevor.sullivan@tufts.edu)
 * @brief Implementation of the Plotter Class
 * @version 0.1
 * @date 2024-09-18
 * 
 * @copyright Copyright (c) 2024
 * 
 */
#include "plotter.h"

#include <string>
#include <iostream>
#include <zmq.hpp>

using namespace std;

Plotter::Plotter():
    context(1),
    pubSock(context, ZMQ_PUB) 
{
    pubSock.bind("tcp://*:5555");
}

void Plotter::sync() {
    zmq::context_t context{1};

    zmq::socket_t socket{context, zmq::socket_type::req};
    socket.connect("tcp://localhost:5556");

    const string data{"sync"};

    cout << "Sending sync..." << endl;
    socket.send(zmq::buffer(data), zmq::send_flags::none);
    
    zmq::message_t reply{};
    socket.recv(reply, zmq::recv_flags::none);

    cout << "Received " << reply.to_string(); 
    cout << endl;
}

void Plotter::sendFrequencyGameData(string buttonPressed, float seconds, int level, float stimRate) {
    string data = buttonPressed + ";" + to_string(seconds) + ";" +  to_string(level) + ";" + to_string(stimRate);

    pubSock.send(zmq::buffer(data));
}

void Plotter::close() {
    const string stop{"stop"};

    pubSock.send(zmq::buffer(stop));
}