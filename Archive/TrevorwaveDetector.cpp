/**
 * @file waveDetector.cpp
 * @author Wesley Clawson (wesley.clawson@tufts.edu). Previous by: Trevor Sullivan (trevor.sullivan@tufts.edu) and Nathan Wu (nathan.wu@yale.edu)
 * @brief Implementation of the WaveDetector Class
 * @version 1.0
 * @date April 2025
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

WaveDetector::WaveDetector() {

}

WaveDetector::WaveDetector(int windowLength, const char *configPath, int framesPerSec, float burst_size_threshold, int burst_dur_threshold,  float BurstOnsetThreshold, float BurstOffsetThreshold) {
    window = new ChannelWindow(windowLength, configPath);

    window->init();

    ElectrodeMap emap = window->electrodeMap();

    this->framesPerSec = framesPerSec;
    this->burst_size_threshold = burst_size_threshold;
    this->burst_dur_threshold = burst_dur_threshold;
    this->BurstOnsetThreshold = BurstOnsetThreshold;
    this->BurstOffsetThreshold = BurstOffsetThreshold;
    totalElectrodes = emap.size();

    metadata = (WaveMetadata *)calloc(1, sizeof(WaveMetadata));

    if (metadata == NULL) {
        cerr << __FILE__ << " line " << __LINE__ << ": metadata memory allocation failed." << endl;
        exit(1);
    }
}

WaveDetector::~WaveDetector() {
    delete window;
    free(metadata);
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

// This is a key method of WaveDetector - it checks to see if a burst is happening and
// does it's best to characterize it's onset and offset, where the peak was, and where
// the burst originiated. 
int WaveDetector::checkBurst(int frameNo) {
    int result = Wave::noBurst;
    int spikeCount = window->totalSpikeCount();

    // Short references to state variables
    bool& isBurstActive = metadata->bursting;
    bool& burstOnsetComplete = metadata->firstBurstDone;
    int& burstOnsetFrame = metadata->burstStartFrame;
    int& burstDurationFrames = metadata->spikeFrameCount;
    int& postBurstQuietFrames = metadata->noSpikeFrameCount;
    int& burstPeakFrame = metadata->maxSpikesFrame;
    int& burstPeakLocation = metadata->maxSpikesLoc;
    int& burstOnsetLocation = metadata->burstStartLocation;
    int& burstOnsetSpikeCount = metadata->burstStartSpikeCount;
    int& maxSpikeCountDuringBurst = metadata->maxSpikes;


    // =====================================================
    //                Over Threshold Logic
    // =====================================================
    if (spikeCount > burst_size_threshold * totalElectrodes) { // This threshold is the lower end of a burst start. (some % of active electrodes)
        result = Wave::bursting;    // will return bursting if queried

        // New burst just started
        if (!isBurstActive) {
            isBurstActive = true;
            burstOnsetFrame = frameNo;
            burstOnsetLocation = window->getAvgX();
            burstOnsetSpikeCount = spikeCount;
            result = Wave::burstStart;
        }

        // This continues to follow the onset of the burst, updating the maxSpikeCountDuringBurst as it goes 
        // as well as the peakFrame and peakLocation (in X).
        if (!burstOnsetComplete &&                      // if the onset is still happening AND
            spikeCount > maxSpikeCountDuringBurst) {    // if the spike count is bigger than the last frame ...
            maxSpikeCountDuringBurst = spikeCount;
            burstPeakFrame = frameNo;
            burstPeakLocation = window->getAvgX();
        } else if (!burstOnsetComplete &&              // if the onset is still happening AND
            spikeCount < maxSpikeCountDuringBurst) {   // the spikes start to dip after the peak (and are still above threshold)...
            burstOnsetComplete = true;
            }

        burstDurationFrames++;      // If you're still above burst threshold, keep tallying how many frames you were
        postBurstQuietFrames = 0;   // Make sure you're not counting QuietFrames

    // =====================================================
    //               Under Threshold Logic
    // =====================================================
    } else {
        postBurstQuietFrames++; // If you're under threshold, keep tallying how many frames you were under

        // If that counter above get's higher than the BurstOffsetThreshold (user set), the burst is considered over.
        // The post burst logic will trigger here. 
        if (postBurstQuietFrames > BurstOffsetThreshold * framesPerSec) {
            isBurstActive = false;

            // If the burst duration recorded was big enough, we consider it 'significant'.
            // Sometimes bursts will dip under threshold really fast, but come back up and we want to ignore that if possible.
            // Mostly because the second peak will be higher, but it doesn't really change the start location. 
            if (burstDurationFrames >= burst_dur_threshold) {
                bool startedOnLeft = burstOnsetLocation < burstPeakLocation;        // KEY: If start location is smaller than peak, it must have started on left. Else, right.
                result = startedOnLeft ? Wave::burstOnLeft : Wave::burstOnRight;

            } else {
                result = Wave::endShortBurst;   // If it wasn't big enough, a this enum is returned to let the user know a shortburst happened.
            }

            // Reset state and be ready for next burst
            burstOnsetComplete = false;
            maxSpikeCountDuringBurst = 0;
            burstDurationFrames = 0;
        }

        // There's no real logic needed for what happens if the burst ends but isn't long enough.
        // If the burst happens again, i.e. a quick double-burst, the stats of the first piece
        // should be kept. 
    }

    return result;
}


//  int WaveDetector::checkBurst(int frameNo) {

//     // ===== Burst Detection State Variables =====
//     //
//     // These variables track the state of a neural spike burst as it unfolds over time.
//     // Inspired by 80/20 burst onset/offset model (see waveform diagram).

//     bool isBurstActive;              // True if a burst is currently in progress.
//     bool burstOnsetComplete;         // True once a burst has reached its peak (onset → peak).
//     int burstOnsetFrame;             // Frame when the burst begins (crosses threshold).
//     int burstDurationFrames;         // Number of frames with elevated spike activity during current burst.
//     int postBurstQuietFrames;        // Number of consecutive frames with low spike activity.
//     int burstPeakFrame;              // Frame at which spike activity peaked.
//     int burstPeakLocation;           // X-location (center of mass) of peak spike activity.
//     int burstOnsetLocation;          // X-location when burst began.
//     int burstOnsetSpikeCount;        // Total spikes at burst start.
//     int maxSpikeCountDuringBurst;    // Highest spike count observed during burst.
    
//     int ret = Wave::noBurst;
//     int spikeCount = window->totalSpikeCount();


//     // If we think a burst starts -> spikeCount (i.e. # of active electrodes) goes above a percentage of total
//     if  (spikeCount > threshold * totalElectrodes) { 
//         ret = Wave::isBurstActive;   // this will make the output of checkBurst be the enum isBurstActive

//         // NOTE: needs more logic here
//         if (!metadata->isBurstActive) {
    
//             // burst started
//             metadata->isBurstActive = true;

//             metadata->burstOnsetLocation = window->getAvgX(); 
//             metadata->burstStartSpikeCount = spikeCount;
//             metadata->burstOnsetFrame = frameNo;

//             ret = Wave::burstStart;
//         }

//         // TODO: add variable for 0.005
//         if (!metadata->burstOnsetComplete && spikeCount > metadata->maxSpikes && frameNo % (int)(framesPerSec * 0.005) == 0){
//             metadata->maxSpikes = spikeCount;
//             metadata->maxSpikesFrame = frameNo;
//             metadata->burstPeakLocation = window->getAvgX();
//         }
        
//         metadata->burstDurationFrames++;        // If there is a burst, start counting how long it's been up
//         metadata->postBurstQuietFrames = 0;    // If there is no burst, reset the counter for how long there's no burst 

//     // no spike in activity
//     } else { 

//         // If the no-burst stretch is long enough (firstBurstThreshold), we declare the burst as "done ramping up"
//         if (!metadata->burstOnsetComplete && metadata->postBurstQuietFrames > firstBurstThreshold * framesPerSec) {
//             metadata->burstOnsetComplete = true; 
//         }

//         // If we decide the burst is over (the no-burst time exceeds burstDoneThreshold * framesPerSec),
//         // set the logic to say it's over and see if it started on the Left or the Right of the chip. 
//         if (metadata->postBurstQuietFrames > burstDoneThreshold * framesPerSec) {
            
//             // We've seen long enough of no burst, set the isBurstActive flag to false
//             metadata->isBurstActive = false;
            
//             // Check to see if the burst is long enough to be significant (minFrames is user set)
//             if (metadata->burstDurationFrames >= minFrames) {
                
//                 bool startLeft = metadata->burstOnsetLocation < metadata->burstPeakLocation;
//                 if (startLeft) {
//                     ret = Wave::leftToRight;
//                 } else {
//                     ret = Wave::rightToLeft;
//                 }

//             } else {
//                 ret = Wave::endShortBurst;
//             }

//             metadata->burstOnsetComplete = false;
//             metadata->maxSpikes = 0;  
//             metadata->burstDurationFrames = 0;
//         }

//         metadata->noburstDurationFrames++;  
//     }

//     return ret;
// }

int WaveDetector::processFrame(maxlab::FilteredFrameData frame, int frameNo) {
    if (window == NULL) {
        cerr << __FILE__ << " line " << __LINE__ << ": window is NULL" << endl;
        exit(1);
    }
    window->shift(frame);

    return checkBurst(frameNo);
}