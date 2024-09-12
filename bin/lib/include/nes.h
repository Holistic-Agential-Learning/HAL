#include "controller.h"
#include <iostream>
#include <fstream>

#ifndef __NES_H__
#define __NES_H__

using namespace std;

class NES : public Controller {
    public:

        NES(float spikePercentThreshold=0.03, float zScoreThreshold=3);

        NES(const char *csvName, float spikePercentThreshold=0.03, float zScoreThreshold=3);

        NES(const char *AconfigPath, const char *BconfigPath, int windowLength, const char *csvName, float spikePercentThreshold=0.03, float zScoreThreshold=3);

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
        void addButton(string id, int windowLength, const char *configPath, int saveWindows=10);

        


    private:
        int currFrame = 0;
        fstream csv;
        float zThresh;
        float percentThresh;
        

};

#endif