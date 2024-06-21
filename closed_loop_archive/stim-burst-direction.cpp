#include <stdlib.h>
#include <stdio.h>
#include <iostream>
#include <unistd.h>
#include "maxlab_lib/include/maxlab/maxlab.h"
#include <signal.h>
#include <vector>

using namespace std;

// amount of time to wait for system startup
#define SYS_START_BUFFER 100000
#define TOTAL_ELECTRODES 1019
#define MIN_FRAMES 3000
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
    int frames = 1*60*20000;
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
    for (int i = 0; i < SYS_START_BUFFER; i++) {
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
    int lastSpike = 0;
    int blanking = 0;
    int spikePeak = 0;
    int spikePeakFrame = 0;
    int spikeStartFrame = 0;
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

        /*
            frameData.spikeEvents (array of spikeEvent type, containing frame num, channel num, and amp)
        */

        if (blanking > 0) {
            blanking--;
            if (blanking != 0) {
                continue;
            }
        }
   
        
        if (spikeCount > threshold * TOTAL_ELECTRODES) {
            if (noSpikeFrameCount > 0 && spikeFrameCount == 0) {
                cout << i << ": Buffer lasting " << noSpikeFrameCount << " frames" << endl;
                spikeStartFrame = i;
                noSpikeFrameCount = 0;
            }
            spikeFrameCount += 1 + noSpikeFrameCount; // spike at this frame
            // spikeFrameCount++;
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
                    int end = i - 201;
                    int rise = spikePeakFrame - spikeStartFrame;
                    int decay = end - spikePeakFrame;
                    int length = end - spikeStartFrame;
                    cout << "----------------------------------" << endl;
                    cout << "Spike lasting " << spikeFrameCount << " frames detected" << endl;
                    cout << "\tlength: " << length << endl;
                    cout << "\tStart: " << spikeStartFrame << endl << "\tEnd: " << end << endl;
                    cout << "\tPeak height: " << spikePeak << endl;
                    cout << "\tRise: " << rise << endl;
                    cout << "\tDecay: " << decay << endl;
                    
                    if (decay > 3 * rise) {
                        maxlab::verifyStatus(maxlab::sendSequence("stim_seq"));
                        cout << i << ": sent stimulation after burst of " << spikeFrameCount << " frames" << endl;
                        blanking = 8000;
                        
                    }
                    cout << "----------------------------------" << endl;
                }
                spikePeak = 0;
                spikeFrameCount = 0;    
            }
            noSpikeFrameCount++;
        }
    } 

    cout << "program over  " << endl;
    maxlab::verifyStatus(maxlab::DataStreamerFiltered_close());

    return 0;
}