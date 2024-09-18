/**
 * @file nes.h
 * @author Trevor Sullivan (trevor.sullivan@tufts.edu)
 * @brief Header file for the NES class 
 * @version 0.1
 * @date 2024-09-18
 * 
 * @copyright Copyright (c) 2024
 * 
 */

#ifndef __NES_H__
#define __NES_H__

#include <fstream>
#include "controller.h"

using namespace std;

class NES : public Controller {
    public:

        /**
         * @brief Construct a new <code>NES</code> object
         * 
         * @param spikePercentThreshold <code>float</code> percent of channels
         *                              that spiked threshold (default 0.03)
         * @param zScoreThreshold <code>float</code> Z score threshold (default
         *                        3)
         */
        NES(float spikePercentThreshold=0.03, float zScoreThreshold=3);

        /**
         * @brief Construct a new <code>NES</code> object
         * 
         * @param csvName <code>const char *</code> full path to csv which holds
         *                button data for post-experiment analysis. If the csv
         *                doesn't exist, it will automatically be created.
         * @param spikePercentThreshold <code>float</code> percent of channels
         *                              that spiked threshold (default 0.03)
         * @param zScoreThreshold <code>float</code> Z score threshold (default
         *                        3)
         */
        NES(const char *csvName, float spikePercentThreshold=0.03, float zScoreThreshold=3);

        /**
         * @brief Construct a new <code>NES</code> object
         * 
         * @param maxtwo <code>bool</code> indicates if the experiment is 
         *               running on the maxtwo
         * @param windowLength <code>int</code> length of the windows 
         *                     representing the buttons, measured in frames
         * @param AconfigPath <code>const char *</code>
         * @param BconfigPath <code>const char *</code>
         * @param csvName <code>const char *</code> full path to csv which holds
         *                button data for post-experiment analysis. If the csv
         *                doesn't exist, it will automatically be created.
         * @param spikePercentThreshold <code>float</code> percent of channels
         *                              that spiked threshold (default 0.03)
         * @param zScoreThreshold <code>float</code> Z score threshold (default
         *                        3)
         */
        NES(bool maxtwo, int windowLength, const char *AconfigPath, const char *BconfigPath, const char *csvName, float spikePercentThreshold=0.03, float zScoreThreshold=3);

        /**
         * @brief Destroy the <code>NES</code> object
         * 
         */
        ~NES();

        /**
         * @brief checks if either button A or button B has been pressed
         * 
         * @param frameNo 
         * @return <code>int</code> code:
         *         -1: button A or B has not been initialized
         *         0: neither button A or B was pressed
         *         1: button A was pressed
         *         2: button B was pressed
         */
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