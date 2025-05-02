/**
 * @file waveDetector.cpp
 * @author Wesley Clawson (wesley.clawson@tufts.edu). Previous by: Trevor Sullivan (trevor.sullivan@tufts.edu) and Nathan Wu (nathan.wu@yale.edu)
 * @brief Implementation of the WaveDetector Class
 * @version 1.0
 * @date 2025-04-29
 * 
 * @copyright Copyright (c) 2025
 * 
 */

// Basic includes
#include <iostream>

// From MaxWell Bio
#include "maxlab.h"

// HAL-based inclusions
#include "waveDetector.h"
#include "channelWindow.h"
#include "electrodeMap.h"

using namespace std;

WaveDetector::WaveDetector() {

}

WaveDetector::WaveDetector(int windowLength, const char *configPath, int fps, float burst_size_threshold, float burst_dur_threshold, float BurstFinishedThreshold) {
    
    window = new ChannelWindow(windowLength, configPath);   // Create a window with the correct parameters. 
    window->init(); // You need to initialze the window using the parameters passed by a user. 

    ElectrodeMap emap = window->electrodeMap(); // This will grab the electrodeMap (includes x positions & number of channels)

    // This section takes the parameters passed into WaveDetector and makes them accessible to across the WaveDetector class.
    // For example, these are 'available' in the checkBurst method. 
    this->framesPerSec = fps;
    this->burst_size_threshold = burst_size_threshold;
    this->burst_dur_threshold = burst_dur_threshold;
    this->BurstFinishedThreshold = BurstFinishedThreshold;
    totalElectrodes = emap.size();

    // Preallocated space for the metadata (current burst information)
    metadata = new WaveMetadata{};

    if (metadata == NULL) {
        cerr << __FILE__ << " line " << __LINE__ << ": metadata memory allocation failed." << endl;
        exit(1);
    }
}

WaveDetector::~WaveDetector() {
    delete metadata;
}

ChannelWindow *WaveDetector::getWindow() {
    return window;
}

WaveMetadata WaveDetector::getMetadata() {
    return *metadata;
}

void WaveDetector::shiftWindow(maxlab::FilteredFrameData frame) {
    window->shift(frame);
}

// Method for processing a frame. It checks if the frame is NULL and if not, 
// move into checkBurst. 
int WaveDetector::processFrame(maxlab::FilteredFrameData frame, int frameNo) {
    if (window == NULL) {
        cerr << __FILE__ << " line " << __LINE__ << ": window is NULL" << endl;
        exit(1);
    }
    shiftWindow(frame);
    return checkBurst(frameNo);
}

void WaveDetector::resetBurstMetadata() {
    metadata->burstOnsetComplete = false;
    metadata->maxSpikes = 0;
    metadata->framesAboveThreshold = 0;
}

// This is a key method of WaveDetector - it checks to see if a burst is happening and
// does it's best to characterize it's onset and offset, where the peak was, and where
// the burst originiated. 
// int WaveDetector::checkBurst(int frameNo) {
//     int result = Wave::noBurst;
//     int spikeCount = window->totalSpikeCount();
//     float burstQuietThresholdFrames = BurstFinishedThreshold * framesPerSec;
//     float burst_dur_thresholdFrames = burst_dur_threshold * framesPerSec;

//     // =====================================================
//     //                Over Threshold Logic
//     // =====================================================
//     if (spikeCount > burst_size_threshold * totalElectrodes) { // This threshold is the lower end of a burst start. (some % of active electrodes)
//         result = Wave::bursting;    // will return bursting if queried

//         // New burst just started
//         if (!metadata->bursting) {
//             metadata->bursting = true;
//             metadata->burstStartFrame = frameNo;
//             metadata->burstStartLocation = window->getAvgX();
//             metadata->burstStartSpikeCount = spikeCount;
//             result = Wave::burstStart;
//         }

//         // This continues to follow the onset of the burst, updating the maxSpikeCountDuringBurst as it goes 
//         // as well as the peakFrame and peakLocation (in X).
//         if (!metadata->burstOnsetComplete &&                   // if the onset is still happening AND
//             spikeCount > metadata->maxSpikes) {                // if the spike count is bigger than the last frame ...
//             metadata->maxSpikes = spikeCount;
//             metadata->maxSpikesFrame = frameNo;
//             metadata->maxSpikesLoc = window->getAvgX();
//         } else if (!metadata->burstOnsetComplete &&           // if the onset is still happening AND
//             spikeCount < metadata->maxSpikes) {               // the spikes start to dip after the peak (and are still above threshold)...
//             metadata->burstOnsetComplete = true;
//         }

//         metadata->framesAboveThreshold++;      // If you're still above burst threshold, keep tallying how many frames you were
//         metadata->noSpikeFrameCount = 0;   // Make sure you're not counting QuietFrames


//     // =====================================================
//     //               Under Threshold Logic
//     // =====================================================
//     } else {
//         metadata->noSpikeFrameCount++; // If you're under threshold, keep tallying how many frames you were under

//         // If that counter above gets higher than the BurstFinishedThreshold (user set), the burst is considered over.
//         // The post burst logic will trigger here. 
//         if (metadata->noSpikeFrameCount >= burstQuietThresholdFrames) {
//             metadata->bursting = false;

//             // If the burst duration recorded was big enough, we consider it 'significant'.
//             // Sometimes bursts will dip under threshold really fast, but come back up and we want to ignore that if possible.
//             // Mostly because the second peak will be higher, but it doesn't really change the start location. 

//             // if (metadata->framesAboveThreshold >= burst_dur_thresholdFrames) {
//             //     bool startedOnLeft = metadata->burstStartLocation < metadata->maxSpikesLoc;        // KEY: If start location is smaller than peak, it must have started on left. Else, right.
//             //     result = startedOnLeft ? Wave::burstOnLeft : Wave::burstOnRight;
//             // } else {
//             //     result = Wave::endShortBurst;   // If it wasn't big enough, this enum is returned to let the user know a short burst happened.
//             // }

//             if (metadata->framesAboveThreshold >= burst_dur_thresholdFrames) {
//                 bool startedOnLeft = metadata->burstStartLocation < metadata->maxSpikesLoc;
//                 result = startedOnLeft ? Wave::burstOnLeft : Wave::burstOnRight;
            
//                 std::cout << "[WaveDetector] Emitting "
//                           << (startedOnLeft ? "burstOnLeft" : "burstOnRight")
//                           << " at frame " << frameNo << std::endl;

//             }else {
//                 // std::cout << "[Burst FAILED duration threshold] "
//                 //           << "framesAboveThreshold = " << metadata->framesAboveThreshold 
//                 //           << " / required = " << burst_dur_thresholdFrames << std::endl;`
            
//                 result = Wave::endShortBurst;
//             }
            

//         }
//         // There's no real logic needed for what happens if the burst ends but isn't long enough.
//         // If the burst happens again, i.e. a quick double-burst, the stats of the first piece
//         // should be kept. 
//     }

//     return result;
// }

int WaveDetector::checkBurst(int currentFrame) {
    int result = Wave::noBurst;

    int spikeCount = window->totalSpikeCount();
    float avgX = window->getAvgX();
    bool aboveThreshold = (static_cast<float>(spikeCount) / totalElectrodes) > burst_size_threshold;

    // if (currentFrame % 100){
    //     std::cout << "[Burst Debug] spikeCount: " << spikeCount
    //         << ", threshold: " << burst_size_threshold * totalElectrodes
    //         << ", currently bursting: " << metadata->bursting << std::endl;
    // }

    if (!metadata->bursting) {
        if (aboveThreshold) {
            // --- Burst just started ---
            metadata->bursting = true;
            metadata->burstStartFrame = currentFrame;
            metadata->burstStartLocation = avgX;
            metadata->burstStartSpikeCount = spikeCount;

            metadata->maxSpikes = spikeCount;
            metadata->maxSpikesFrame = currentFrame;
            metadata->maxSpikesLoc = avgX;

            metadata->framesAboveThreshold = 1;
            metadata->noSpikeFrameCount = 0;
            burstStarted = true;

            result = Wave::burstStart;
        }
    } else {  // currently bursting
        if (aboveThreshold) {
            metadata->framesAboveThreshold++;
            metadata->noSpikeFrameCount = 0;

            if (spikeCount > metadata->maxSpikes) {
                metadata->maxSpikes = spikeCount;
                metadata->maxSpikesFrame = currentFrame;
                metadata->maxSpikesLoc = avgX;
            }

            // No need to emit burstStart again
            result = Wave::bursting;

        } else {
            metadata->noSpikeFrameCount++;

            if (metadata->noSpikeFrameCount >= BurstFinishedThreshold * framesPerSec) {
                
                // --- Burst ending ---
                metadata->bursting = false;
                burstStarted = false;

                int durThreshFrames = static_cast<int>(burst_dur_threshold * framesPerSec);
                if (metadata->framesAboveThreshold >= durThreshFrames) {
                    bool startedOnLeft = metadata->burstStartLocation < metadata->maxSpikesLoc;
                    result = startedOnLeft ? Wave::burstOnLeft : Wave::burstOnRight;
                } else {
                    result = Wave::endShortBurst;
                }
            }
        }
    }

    return result;
}
