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
         * documentation for Wave enum
         *
        */
        enum Wave {noBurst, bursting, burstStart, endShortBurst, leftToRight, rightToLeft};

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
        WaveDetector(int windowLength, const char *configPath, float threshold, int minFrames, int frameHz=10000);
        ~WaveDetector();

        void shiftWindow(maxlab::FilteredFrameData frame);

        // value corresponds to Wave enum
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