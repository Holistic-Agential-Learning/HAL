#include "controller.h"

#ifndef __NES_H__
#define __NES_H__

using namespace std;

class NES : public Controller {
    public:

        /**
         * @brief Adds a new button (ChannelWindow) to the Controller 
         * 
         * @param id <code>string</code> identifier of the button/config
         * @param windowLength <code>int</code> length of the window
         * @param configPath <code>char</code> array representing the full path 
         *                  of the config file
         * @param saveWindows <code>int</code> indicating how many windows to 
         *                  save, default 0
         */
        void addButton(string id, int windowLength, const char *configPath, int saveWindows=0);


    private:
        

};

#endif