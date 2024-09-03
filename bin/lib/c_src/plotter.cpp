#include "plotter.h"
#include <string>
#include <iostream>

Plotter::Plotter() {
    zmq::context_t context{1};
    pubSock = zmq::socket_t(context, ZMQ_PUB);
    pubSock.bind("tcp://*:5555");
}

void Plotter::sync() {
    zmq::context_t context{1};

    zmq::socket_t socket{context, zmq::socket_type::req};
    socket.connect("tcp://localhost:5556");

    const std::string data{"sync"};

    std::cout << "Sending sync..." << std::endl;
    socket.send(zmq::buffer(data), zmq::send_flags::none);
    
    zmq::message_t reply{};
    socket.recv(reply, zmq::recv_flags::none);

    std::cout << "Received " << reply.to_string(); 
    std::cout << std::endl;
}

void Plotter::sendFrequencyGameData(string buttonPressed, float seconds, int stimLevel, float stimRate) {
    string data = buttonPressed + ";" + to_string(seconds) + ";" +  to_string(stimLevel) + ";" + to_string(stimRate);

    pubSock.send(zmq::buffer(data));
}

void Plotter::close() {
    const std::string stop{"stop"};

    pubSock.send(zmq::buffer(stop));
}