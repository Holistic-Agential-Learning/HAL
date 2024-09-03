#ifndef __PLOTTER_H__
#define __PLOTTER_H__

#include <string>
#include <zmq.hpp>

using namespace std;

class Plotter {
    public: 
        /**
         * @brief Construct a new Plotter object
         */
        Plotter();

        /**
         * @brief Syncs with Python plotter. Note that this function will 
         * block until the plotter is ready.
         * 
         * 
         */
        void sync();

        void sendFrequencyGameData(string buttonPressed, float seconds, int stimLevel, float stimRate);

        /**
         * @brief Closees the plotter connection
         * 
         */
        void close();

    private:
        zmq::context_t context;
        zmq::socket_t pubSock;
};

#endif