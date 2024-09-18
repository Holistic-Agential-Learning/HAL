/**
 * @file plotter.h
 * @author Trevor Sullivan (trevor.sullivan@tufts.edu)
 * @brief Header file for the Plotter Class
 * @version 0.1
 * @date 2024-09-18
 * 
 * @copyright Copyright (c) 2024
 * 
 */

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

        /**
         * @brief sends data to python plotter for real-time plotting
         * 
         * This function MUST be called only after syncing both end of the 
         * plotter.
         * 
         * @param buttonPressed <code>string</code> the button that was pressed
         * @param seconds <code>float</code> the current frame, converted to
         *                seconds
         * @param level <code>int</code> the "level" in the frequency space
         * @param stimRate <code>float</code> the current rate of stimulation, 
         *                 or whatever is being affected by the level
         */
        void sendFrequencyGameData(string buttonPressed, float seconds, int level, float stimRate);

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