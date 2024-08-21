#include <stdlib.h>
#include <stdio.h>
#include <iostream>
#include <unistd.h>
#include "maxlab_lib/include/maxlab/maxlab.h"
#include <signal.h>

using namespace std;
#define BUFFER_TIME 100000
#define TOTAL_ELECTRODES 1019
#define MIN_FRAMES 1
#define SCAN_FRAMES 200
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

    cout << "Processing " << frames << " frames of neuron activity with a \
    spike threshold of " << threshold << endl;
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
    int bi = 0;

    for (int i = 0; i < frames; i++) {
        maxlab::FilteredFrameData frameData;
        maxlab::Status status = maxlab::DataStreamerFiltered_receiveNextFrame(&frameData);

        // If no data was read in, try again (happens when loop finishes before 
        // the machine takes another sample)
        if (status == maxlab::Status::MAXLAB_NO_FRAME) {
            i--;
            continue;
        }
   
        if  (bi <= SCAN_FRAMES) {
            spikeWindowCount += frameData.spikeCount;  
            bi++;
        } else {
            bi = 0;
            // cout << (spikeWindowCount) << " vs " << (threshold * TOTAL_ELECTRODES) << endl;
            if (spikeWindowCount >= threshold * TOTAL_ELECTRODES) {
                spikeFrameCount++;
                // cout << "Spike detected" << endl;
            } else { 
                if (spikeFrameCount >= MIN_FRAMES) {
                    double burst_dur = spikeFrameCount*SCAN_FRAMES/(double)FRAMES_PER_SEC;
                    cout << (spikeFrameCount) << " number of windows detected, length: ~" << (burst_dur) << " sec" << endl;
                }
                spikeFrameCount = 0;
            }
            spikeWindowCount = 0;
        }
    } 

    maxlab::verifyStatus(maxlab::DataStreamerFiltered_close());

    return 0;
}