/**
 * @file well.h
 * @author Emily Ertle (emily.ertle@tufts.edu)
 * @brief Header file for the Well Class
 * @version 1.0
 * @date 2025-05-16
 * 
 * @copyright Copyright (c) 2025
 * 
 */

#ifndef __WELL_H__
#define __WELL_H__

#include "maxlab.h"
#include <memory>

using namespace std;

/**
 * @struct ExperimentState
 * @brief Struct for holding the internal state of the experiment during training.
 */
struct ExperimentState {
    bool bursting = false;      // this should get thrown if there's a true burst 
    bool burstStart = false;    // this is if the threshold is crossed, but not a full burst yet
    int blanking = 0;
    int previousBurst = 0;
    int lastBurstStartFrame = 0;
}; 

class Well {
    public:

        /**
         * @brief Constructs a new Well object
         */
        Well();
        /**
         * @brief Constructs a new Well object with parameters
         * 
         * @param wellID <code>int</code> ID of well
         * @param framesPerSec <code>int</code> sampling rate (based on device type)
         * @param rightBurst <code>int</code> indicates stimulation type
         * @param leftBurst <code>int</code> indicates stimulation type
         * @param stimRate <code>float</code> stimulation rate
         * @param configPath c-style string containing the full path of the electrode config
         * @param burstSizeThreshold <code>float</code> fraction of active electrodes needed to start a burst
         * @param burstDurThreshold <code>float</code> minimum burst duration (in seconds)
         * @param pulseDurationSecs <code>float</code> duration of stimulation pulse (in seconds)
         */
        Well(int wellID, int framesPerSec, int rightBurst, int leftBurst, float stimRate, 
        const char *configPath, float burstSizeThreshold, float burstDurThreshold, float pulseDurationSecs);

        /**
         * @brief Destroys the Well object
         */
        ~Well();



    private:
        const int WELL_ID;
        const int WINDOW;
        const int BLANKING_FRAMES;

        std::unique_ptr<WaveDetector> sensor;
        std::unique_ptr<ChannelWindow> window;
        std::unique_ptr<ExperimentState> state;
        std::unique_ptr<StimVector> rightStim;
        std::unique_ptr<StimVector> leftStim;

        int framesPerSec;
        std::ofstream file;

        const int CAPACITY = 10;

        int locCounter = 0;
        float locs[CAPACITY] = {0.0};
        int burstSpikeCounts[CAPACITY] = {0};
        int waveVal = 0;
        int spikeCount = 0;
        bool directionHandled = false;

};

#endif