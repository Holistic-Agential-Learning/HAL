/**
 * @file waveDetector.h
 * @author Wesley Clawson (wesley.clawson@tufts.edu). Previous by: Trevor Sullivan (trevor.sullivan@tufts.edu)
 * @brief Header file for the WaveDetector Class
 * @version 1.0
 * @date 2025-04-29
 * 
 * @copyright Copyright (c) 2025
 * 
 */

#ifndef __WAVEDETECTOR_H__
#define __WAVEDETECTOR_H__

#include "maxlab.h"
#include "channelWindow.h"

using namespace std;

/**
 * @struct WaveMetadata
 * @brief Metadata tracking the state of a neural burst event
 */
struct WaveMetadata {
    bool burstOnsetComplete;        /**< True once the burst has peaked and started to fall */
    bool bursting;                  /**< True while a burst is active */
    
    int burstStartFrame;             /**< Frame when the burst started */
    int burstStartSpikeCount;        /**< Spike count when burst started */
    float burstStartLocation;        /**< X-location of onset of burst */

    int maxSpikes;                   /**< Peak spike count observed during burst */
    int maxSpikesFrame;              /**< Frame when peak spike count occurred */
    float maxSpikesLoc;              /**< X-location where peak spike count occurred */

    int framesAboveThreshold;        /**< Number of frames the spike count stayed above threshold */
    int noSpikeFrameCount;            /**< Number of frames spike count stayed below threshold */
};

/**
 * @brief Wave enum
 * 
 */
enum Wave {
    noBurst,         /**< Culture is not currently bursting */
    bursting,        /**< Culture is currently bursting */
    burstStart,      /**< Burst just started */
    endShortBurst,   /**< Burst ended but was too short to be significant */
    burstOnLeft,     /**< Burst ended, and it started on the Left */
    burstOnRight     /**< Burst ended, and it started on the Right */
};

class WaveDetector {
    public:

        /**
         * @brief Constructs a new Wave Detector object
         */
        WaveDetector();

        /**
         * @brief Constructs a new Wave Detector object and initializes the 
         *        window
         * 
         * @param windowLength <code>int</code> length of the window
         * @param configPath c-style string containing the full path of the 
         *                   electrode config
         * @param framesPerSec <code>int</code> sampling rate in frames per second
         * @param burst_size_threshold <code>float</code> fraction of active electrodes needed to start a burst
         * @param burst_dur_threshold <code>float</code> minimum burst duration (in seconds)
         * @param BurstFinishedThreshold <code>float</code> minimum time (in seconds) of low activity to confirm burst ended
         */
        WaveDetector(int windowLength, const char *configPath, int framesPerSec, float burst_size_threshold, float burst_dur_threshold, float BurstFinishedThreshold);

        /**
         * @brief Destroys the Wave Detector object
         */
        ~WaveDetector();

        /**
         * @brief Returns the window
         * 
         * @return pointer to <code>ChannelWindow</code>
         */
        ChannelWindow *getWindow();

        /**
         * @brief Gets metadata of the Wave Detector
         * 
         * @return <code>WaveMetadata</code> struct
         */
        WaveMetadata getMetadata();

        /**
         * @brief Shifts the window, adding a new frame
         * 
         * @param frame <code>maxlab::FilteredFrameData</code> frame to add to 
         *              the window
         */
        void shiftWindow(maxlab::FilteredFrameData frame);

        /**
         * @brief Processes a frame
         * 
         * Shifts the window, and returns the status of the burst
         * 
         * @param frame <code>maxlab::FilteredFrameData</code> frame to 
         *              process
         * @param frameNo <code>int</code> frame number when <code>frame</code>
         *                was received
         * @return <code>int</code>
         */
        int processFrame(maxlab::FilteredFrameData frame, int frameNo);

        /**
         * @brief Checks the direction of a burst
         * 
         * @param frameNo <code>int</code> frame number of the most recently 
         *                received frame
         * @return <code>int</code>, corresponds to <code>enum Wave</code> 
         */
        int checkBurst(int frameNo);

        /**
        * @brief Resets burst-related metadata after a burst is processed.
        */
        void resetBurstMetadata();

    private:
        ChannelWindow *window;

        WaveMetadata *metadata;
        int framesPerSec;
        int totalElectrodes;
        float burst_size_threshold;
        float burst_dur_threshold;
        float BurstFinishedThreshold;
        bool burstStarted = false;
};

#endif