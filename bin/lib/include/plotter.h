#ifndef __PLOTTER_H__
#define __PLOTTER_H__

#include <string>

class Plotter {
    public: 
        /**
         * @brief Construct a new Plotter object
         * 
         * @param experiment_type <code>string</code> representing the type of 
         *                        experiment being run. Currently, only 
         *                        "frequency_game" is supported.
         */
        Plotter(string experiment_type="frequency_game");

        /**
         * @brief Syncs with Python plotter 
         * 
         * 
         */
        void sync();

    private:

        // currrently supports "frequency_game"
        string type;
        zmq::socket_t pub_sock;
};

#endif