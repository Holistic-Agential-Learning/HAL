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
    
    int noSpikeFrameCount; /**< number of frames since the total spike 
                                count went over the threshold*/

    int burstStartLocation; /**< starting location of the current or 
                                    most recent burst*/

    int burstStartSpikeCount; /**< starting spike count of the current 
                                    or most recent burst*/

    int burstStartFrame; /**< starting frame of the current or most 
                                recent burst*/

    int burstEnd; /**< frame when the last burst ended*/
    
    int maxSpikes; /**< spike count of the peak of the burst (or most 
                        recent peak within the burst)*/

    int maxSpikesFrame; /**< frame number where the peak of the burst 
                                occured (or most recent peak within the 
                                burst)*/

    float maxSpikesLoc; /**< locatin on the chpi of the peak of the 
                                burst (or most recent peak within the 
                                burst)*/
}; 

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

typedef struct WaveMetadata WaveMetadata;


class WaveDetector {
    public:

        /**
         * @brief Constructs a new Wave Detector object
        */
        WaveDetector();

        /**
         * @brief Constructs a new Wave Detector object and inititalizes the 
         *        window
         * 
         * @param windowLength <code>int</code> length of the window
         * @param configPath c-style string containing the full path of the 
         *                   electrode config
         * @param threshold <code>float</code> threshold used to check the total 
         *                  spike count against
         * @param minFrames <code>int</code> minimum number of frames 
         *                  during which the window must be over the spike 
         *                  threshold in order to be considered a burst
         * @param frameHz <code>int</code> framerate, defaults
         *                to <code>10000</code>. It shoud be <code>10000</code> for the 
         *                MaxTwo, and <code>20000</code> for the MaxOne
         * @param firstBurstThreshold <code>float</code> the amount of time (in
         *                            seconds) during which the total spike
         *                            count of the window cannot go over the 
         *                            threshold in order for the first birst to 
         *                            be considered done.
         * @param burstDoneThreshold <code>float</code> the amount of time (in 
         *                           seconds) during which the total spike
         *                            count of the window cannot go over the 
         *                            threshold in order for the entire birst to 
         *                            be considered done.
         */
        WaveDetector(int windowLength, const char *configPath, float threshold, int minFrames, int frameHz, float firstBurstThreshold, float burstDoneThreshold);
        
        /**
         * @brief Destroys the Wave Detector Object 
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

    private:
        ChannelWindow *window;

        WaveMetadata *metadata;
        int framesPerSec;
        int minFrames;
        float threshold;
        int totalElectrodes;
        float firstBurstThreshold;
        float burstDoneThreshold;

};

#endif