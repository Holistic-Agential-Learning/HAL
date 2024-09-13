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

        NES(bool maxtwo, int windowLength, const char *AconfigPath, const char *BconfigPath, const char *csvName, float spikePercentThreshold=0.03, float zScoreThreshold=3);

        ~NES();

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
        // void addButton(string id, int windowLength, const char *configPath, int saveWindows=10);

        int checkButtons(int frameNo);

        


    private:
        int currFrame = 0;
        std::fstream csv;
        float zThresh;
        float percentThresh;
        bool aReleased;
        bool bReleased;

        float zScore(float value, float avg, float sd);
        void printValues(int ab, int frameNo, float perA, float valA, float avgA, float sdA, float zA, float perB, float valB, float avgB, float sdB, float zB);
        

};

#endif