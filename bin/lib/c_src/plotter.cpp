#include "plotter.h"
#include <zmq.hpp>
#include <stdlib.h>
#include <stdio.h>

Plotter::Plotter(string experiment_type) {
    type = experiment_type;

    zmq::context_t context{1};
    pub_sock{context, ZMQ_PUB};
    socket.bind("tcp://*:5555");
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