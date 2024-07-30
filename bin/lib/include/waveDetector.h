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
         * @brief Wave enum
         * 
         */
        enum Wave {
            noBurst, /**< culture is not currently bursting */
            bursting, /**< culture is currently bursting */
            burstStart, /**< burst just started */
            endShortBurst, /**< burst ended, but it was too short to be 
                                significant*/
            leftToRight, /**< burst ended, and it went left to right*/
            rightToLeft /**< burst ended, and it went right to left*/
        };

        /**
         * @struct WaveMetadata
         * @brief Wave metadata struct
         * 
         */
        struct WaveMetadata {
            bool firstBurstDone; /**< indicates first burst is done*/
            bool bursting; /**< indicates if currently bursting*/

            int spikeFrameCount; /**< number of frames since the total spike 
                                      count was below the threshold*/

            int burstStartLocation; /**< starting location of the current or 
                                          most recent burst*/
            int burstStartSpikeCount; /**< starting spike count of the current 
                                            or most recent burst*/
            int burstStartFrame; /**< starting frame of the current or most 
                                      recent burst*/

            int burstEnd; /**< frame when the last burst ended*/

            int noSpikeFrameCount; /**< number of frames since the total spike 
                                        count went over the threshold*/
            
            int maxSpikes; /**< spike count of the peak of the burst (or most 
                                recent peak within the burst)*/

            int maxSpikesFrame; /**< frame number where the peak of the burst 
                                      occured (or most recent peak within the 
                                      burst)*/

            float maxSpikesLoc; /**< locatin on the chpi of the peak of the 
                                      burst (or most recent peak within the 
                                      burst)*/
        }; 

        typedef struct WaveMetadata WaveMetadata;

        /**
         * @brief Constructs a new Wave Detector object
        */
        WaveDetector();

        /**
         * @brief Constructs a new Wave Detector object
         * 
         * @param windowLength 
         * @param configPath 
         * @param threshold 
         * @param minFrames 
         * @param frameHz 
         */
        WaveDetector(int windowLength, const char *configPath, float threshold, int minFrames, int frameHz=10000);
        
        /**
         * @brief Destroys the Wave Detector Object 
         */
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