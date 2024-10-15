#include <string>
#include <iostream>
#include <thread>
#include <chrono>
#include <stdlib.h>

#include <zmq.hpp>

using namespace std;
using namespace std::chrono_literals;

int sync() {
    // initialize the zmq context with a single IO thread
    zmq::context_t context{1};

    // construct a REQ (request) socket and connect to interface
    zmq::socket_t socket{context, zmq::socket_type::req};
    socket.connect("tcp://localhost:5556");

    // set up some static data to send
    const std::string data{"sync"};

    // send the request message
    std::cout << "Sending sync..." << std::endl;
    socket.send(zmq::buffer(data), zmq::send_flags::none);
    
    // wait for reply from server
    zmq::message_t reply{};
    socket.recv(reply, zmq::recv_flags::none);

    std::cout << "Received " << reply.to_string(); 
    std::cout << std::endl;

    return 0;
}

int main()
{
    // initialize the zmq context with a single IO thread
    zmq::context_t context{1};

    // construct a REQ (request) socket and connect to interface
    zmq::socket_t socket{context, ZMQ_PUB};
    cout << "connecting..." << endl;
    socket.bind("tcp://*:5555");
    cout << "successfully connected" << endl;
    // set up some static data to send
    sync();
    // const std::string data{"Hello"};

    const std::string stop{"stop"};

    
    int stim_level = 5;
    for (auto time = 0; time < 100; ++time) 
    {
        int aOrB = rand() % 2;
        string ab = aOrB ? "A" : "B";
        if (ab == "A" && stim_level > 0) {
            stim_level--;
        } else if (ab == "B" && stim_level < 10) {
            stim_level++;
        }

        string data = ab + ";" + to_string(stim_level) + ";" + to_string(time);
        // send the request message
        // socket.send(zmq::str_buffer("topic"), zmq::send_flags::sndmore);
        socket.send(zmq::buffer(data));
        
        // // wait for reply from server
        // zmq::message_t reply{};
        // socket.recv(reply, zmq::recv_flags::none);

        // std::cout << "Received " << reply.to_string(); 
        // std::cout << " (" << request_num << ")";
        // std::cout << std::endl;
        std::this_thread::sleep_for(1s);
    }
    socket.send(zmq::buffer(stop));
    // cout << "terminating..." << endl;
    // const std::string stop{"stop"};
    // socket.send(zmq::buffer(data), zmq::send_flags::none);

    return 0;
}
