/**
 * @file waveDetector.cpp
 * @author Wesley Clawson (wesley.clawson@tufts.edu). Previous by: Trevor Sullivan (trevor.sullivan@tufts.edu) and Nathan Wu (nathan.wu@yale.edu)
 * @brief Implementation of the WaveDetector Class - used anytime you need to detect bursts. 
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
    metadata->bursting = false;
    metadata->maxSpikes = 0;
    metadata->framesAboveThreshold = 0;
    metadata->burstStartFrame = 0;
    metadata->burstStartLocation = 0;
    metadata->burstStartSpikeCount = 0;
    metadata->maxSpikes = 0;
    metadata->maxSpikesFrame = 0;
    metadata->maxSpikesLoc = 0;
    metadata->framesUnderThreshold = 0;
}

int WaveDetector::checkBurst(int currentFrame) {

    // Vars used in the logic of the loop.
    int spikeCount = window->totalSpikeCount();
    float avgX = window->getMedX();
    bool aboveThreshold = (static_cast<float>(spikeCount) / totalElectrodes) > burst_size_threshold;
    int durThreshFrames = static_cast<int>(burst_dur_threshold * framesPerSec);
    int burstDoneThreshFrames = static_cast<int>(BurstFinishedThreshold * framesPerSec);

    // A nice debug statement
    // if (currentFrame % 500){
    //     std::cout << "[Burst Debug] spikeCount: " << spikeCount
    //         << ", threshold: " << burst_size_threshold * totalElectrodes
    //         << ", currently bursting: " << metadata->bursting << std::endl;
    // }

    // This forces 'noBurst' every frame unless result gets reset somewhere in the loop below. 
    int result = Wave::noBurst;

    if (!burstStarted){                                 // If there has been no burst start, think like this
        
        if (aboveThreshold) {                           
            // --- Burst just started ---
            metadata->framesAboveThreshold++;
            metadata->burstStartFrame = currentFrame;
            metadata->burstStartLocation = avgX;
            metadata->burstStartSpikeCount = spikeCount;
            metadata->maxSpikes = spikeCount;
            metadata->maxSpikesFrame = currentFrame;
            metadata->maxSpikesLoc = avgX;
            metadata->framesUnderThreshold = 0;
            burstStarted = true;
            result = Wave::burstStart;     
        } 

    } else if (burstStarted && !metadata->bursting){    // If the burst has started but it's not been long enough, do this
        if (aboveThreshold) {
            
            // --- Burst started and is continuing ---
            metadata->framesAboveThreshold++;
            metadata->framesUnderThreshold = 0;
            if (spikeCount > metadata->maxSpikes) {
                metadata->maxSpikes = spikeCount;
                metadata->maxSpikesFrame = currentFrame;
                metadata->maxSpikesLoc = avgX;
            }

            result = Wave::burstStart;

            if (metadata->framesAboveThreshold >= durThreshFrames){
                metadata->bursting = true;
                result = Wave::bursting;
            }
        }
        else {
            metadata->framesUnderThreshold++;          // If you dip under Threshold, start counting
            
            if (metadata->framesUnderThreshold >= burstDoneThreshFrames) { // if you stay under too long, you reset
                metadata->framesAboveThreshold = 0;     
                result = Wave::endShortBurst;
                burstStarted = false;
            }
        } 
    } else if (metadata->bursting){                     // If the culture is bursting, do this
        if (aboveThreshold) {
            metadata->framesAboveThreshold++;
            metadata->framesUnderThreshold = 0;

            if (spikeCount > metadata->maxSpikes) {
                metadata->maxSpikes = spikeCount;
                metadata->maxSpikesFrame = currentFrame;
                metadata->maxSpikesLoc = avgX;
            }

            // It says that we're continuing bursting
            result = Wave::bursting;

        } else {    // This is the logic for when it dips below treshold
            metadata->framesUnderThreshold++;

            if (metadata->framesUnderThreshold >= burstDoneThreshFrames) {
                
                // --- Burst ending ---
                metadata->bursting = false;
                
                if (metadata->framesAboveThreshold >= durThreshFrames) {
                    bool startedOnLeft = metadata->burstStartLocation < metadata->maxSpikesLoc;
                    result = startedOnLeft ? Wave::burstOnLeft : Wave::burstOnRight;
                    burstStarted = false;
                } else {        // at the moment I think this never would get triggered, but I don't care. 
                    result = Wave::endShortBurst;
                    burstStarted = false;
                }
            }
        }
    }

    return result;
}
