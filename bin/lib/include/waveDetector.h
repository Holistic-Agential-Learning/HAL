#include <string>
#include "electrodeMap.h"
#include "channelWindow.h"
#include <vector>
#include <maxlab.h>
#include <stdlib.h>
#include <iostream>
#include <fstream>
#include <map>
#include <utility>

#ifndef __WAVEDETECTOR_H__
#define __WAVEDETECTOR_H__

using namespace std;


class WaveDetector {
    public:

        /**
         * @brief 
         * 
         */
        enum Wave {noBurst, bursting, burstStart, endShortBurst, leftToRight, rightToLeft};

        /**
         * @brief 
         * 
         */
        struct WaveMetadata {
            bool firstBurstDone;
            bool bursting;

            int spikeFrameCount;

            int burstStartLocation;
            int burstStartSpikeCount;
            int burstStartFrame;

            int burstEnd;

            int noSpikeFrameCount;

            int maxSpikesFrame;

            int maxSpikes;

            float maxSpikesLoc;
        }; 

        typedef struct WaveMetadata WaveMetadata;

        /**
         * @brief Constructor
        */
        WaveDetector();

        /**
         * @brief Construct a new Wave Detector object
         * 
         * @param windowLength 
         * @param configPath 
         * @param threshold 
         * @param minFrames 
         * @param frameHz 
         */
        WaveDetector(int windowLength, const char *configPath, float threshold, int minFrames, int frameHz=10000);
        ~WaveDetector();

        /**
         * @brief 
         * 
         * @param frame 
         */
        void shiftWindow(maxlab::FilteredFrameData frame);

        // value corresponds to Wave enum

        /**
         * @brief 
         * 
         * @param frameNo 
         * @return int 
         */
        int checkBurst(int frameNo);

    private:
        ChannelWindow *window;

        WaveMetadata *metadata;
        int framesPerSec;
        int minFrames;
        float threshold;
        int totalElectrodes;

};

#endif