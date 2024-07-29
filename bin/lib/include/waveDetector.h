#include <string>
#include "electrodeMap.h"
#include "channelWindow.h"
#include <vector>
#include <maxlab.h>
#include <stdlib.h>
#include <iostream>
#include <fstream>
#include <map>

#ifndef __WAVEDETECTOR_H__
#define __WAVEDETECTOR_H__

using namespace std;


class WaveDetector {
    public:

        WaveDetector();
        WaveDetector(int windowLength, const char *configPath, float threshold, int frameHz=10000);
        ~WaveDetector();

        void shiftWindow(maxlab::FilteredFrameData frame);
        // void checkBurst();

    private:
        ChannelWindow *window;

        int framesPerSec;

        int totalElectrodes;
        float threshold;

        int spikeFrameCount;

        int burstStart;
        int burstEnd;

        int noSpikeFrameCount;

        bool firstBurstDone;
        int maxSpikesFrame;
        int maxSpikes;

        float maxSpikesLoc;
        int locCounter;
        float monitoringLoc;

        int previousBurstInDesiredDirection;
        bool bursting;

};

#endif