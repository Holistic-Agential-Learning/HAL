/* print-bursts.cpp
 *
 * Prints whenever neurons burst.
 * 
 * Bursts must last longer than 5 frames and the spikes on each frame must be 
 * higher than the given threshold. 
 * 
 */

#include <stdlib.h>
#include <stdio.h>
#include <iostream>
#include <unistd.h>
#include "maxlab_lib/include/maxlab/maxlab.h"
#include <signal.h>
#include <vector>

using namespace std;
#define BUFFER_TIME 100000
#define TOTAL_ELECTRODES 1019
#define MIN_FRAMES 5
#define WINDOW 200
#define FRAMES_PER_SEC 20000

void signal_interrupt_handler(int sig) {
    cout << "^C signalled!" << endl;
    maxlab::verifyStatus(maxlab::DataStreamerFiltered_close());
    exit(sig);
}

// run with ./prints-bursts frames threshold
int main(int argc, char * argv[]) {
    // default process 1200000 frames (1 minute)
    int frames = 1200000;
    float threshold = 0.1;
    
    if (argc >= 2) {
        frames = stoi(argv[1]);
    } if (argc >= 3) {
        threshold = stof(argv[2]);
    }

    cout << "Processing " << frames << " frames of neuron activity with a spike threshold of " << threshold << endl;
    signal(SIGINT, signal_interrupt_handler);

    // Keep in mind that start up causes a lot of spikes

    // Open data stream and check that no errors occurred
    maxlab::verifyStatus(maxlab::DataStreamerFiltered_open(maxlab::FilterType::IIR));
    
    // don't record the system startup stuff
    for (int i = 0; i < BUFFER_TIME; i++) {
        maxlab::FilteredFrameData frameData;
        maxlab::Status status = maxlab::DataStreamerFiltered_receiveNextFrame(&frameData);
        if (status == maxlab::Status::MAXLAB_NO_FRAME) {
            i--;
            continue;
        }
    }
    cout << "Finished buffer, looking for spikes..." << endl;
    // cout << threshold * TOTAL_ELECTRODES << endl;

    int spikeWindowCount = 0;
    int spikeFrameCount = 0;
    int noSpikeFrameCount = 0;
    int spikeCount = 0;
    int spikePeak = 0;
    int spikePeakFrame = 0;
    int spikeStartFrame = 0;
    int lastSpike = 0;
    vector<int> window;
    cout << "Initial vector size: " << window.size() << endl;

    // initialize the vector with 200 frames
    for (int i = 0; i < WINDOW; i++) {
        maxlab::FilteredFrameData frameData;
        maxlab::Status status = maxlab::DataStreamerFiltered_receiveNextFrame(&frameData);

        if (status == maxlab::Status::MAXLAB_NO_FRAME) {
            i--;
            continue;
        }
        spikeCount += frameData.spikeCount;
        window.push_back(frameData.spikeCount);
    }

    for (int i = 0; i < frames; i++) {
        maxlab::FilteredFrameData frameData;
        maxlab::Status status = maxlab::DataStreamerFiltered_receiveNextFrame(&frameData);

        // If no data was read in, try again (happens when loop finishes before 
        // the machine takes another sample)
        if (status == maxlab::Status::MAXLAB_NO_FRAME) {
            i--;
            continue;
        }

        int oldSpikeCount = window[0];
        window.erase(window.begin());
        spikeCount -= oldSpikeCount; 
        spikeCount += frameData.spikeCount;
        window.push_back(frameData.spikeCount);
   
        // if this is a spike
        if  (spikeCount > threshold * TOTAL_ELECTRODES) {
            // Prints downtime between spikes
            if (noSpikeFrameCount > 0 && spikeFrameCount == 0) {
                // cout << i << ": Buffer lasting " << noSpikeFrameCount << " frames" << endl;
                spikeStartFrame = i;
            }
            spikeFrameCount++; // spike at this frame

            // check for peak
            if (spikeCount > spikePeak) {
                spikePeak = spikeCount;
                spikePeakFrame = i;
            }

            noSpikeFrameCount = 0;
        } else {
            // cout << (spikeWindowCount) << " vs " << (threshold * TOTAL_ELECTRODES) << endl;
             
            if (noSpikeFrameCount > 200) {
                if (spikeFrameCount >= MIN_FRAMES) {
                    cout << "----------------------------------" << endl;
                    cout << "Spike lasting " << spikeFrameCount << " frames detected" << endl;
                    cout << "\tStart: " << spikeStartFrame << endl << "\tEnd: " << i << endl;
                    cout << "\tPeak height: " << spikePeak << endl;
                    cout << "\tRise: " << spikePeakFrame - spikeStartFrame << endl;
                    cout << "\tDecay: " << i - spikePeakFrame << endl;
                    cout << "----------------------------------" << endl;
                    spikePeak = 0;
                }      
                spikeFrameCount = 0;  
            }
            noSpikeFrameCount++;
        }
    } 

    cout << "program over  " << endl;
    maxlab::verifyStatus(maxlab::DataStreamerFiltered_close());

    return 0;
}