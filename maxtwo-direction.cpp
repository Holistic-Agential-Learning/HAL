#include <stdlib.h>
#include <stdio.h>
#include <iostream>
#include <unistd.h>
#include <maxlab.h>
#include <signal.h>
#include <vector>
#include <unistd.h>
#include <fstream>
#include "lib/electrodeMap.h"

using namespace std;
using namespace maxlab;

// 220 x 120

// amount of time to wait for system startup
#define SYS_START_BUFFER 100000
#define TOTAL_ELECTRODES 1019
#define MIN_FRAMES 2000
#define WINDOW 200
#define FRAMES_PER_SEC 10000
#define CHIP_WIDTH 220  //87
#define CHIP_HEIGHT 120

float get_avg_side(vector<const SpikeEvent *> spikeEvents, vector<int> spikeCounts, ElectrodeMap emap);
int get_side_diff(vector<const SpikeEvent *> spikeEvents, vector<int> spikeCounts);
float framesToSeconds(int frames);


/* signal_interrupt_handler
 * 
 * Closes the DataStreamer when ^c is signalled.
 * 
 */
void signal_interrupt_handler(int sig) {
    cout << " signalled!" << endl;
    maxlab::verifyStatus(maxlab::DataStreamerFiltered_close());
    exit(sig);
}

// run with ./prints-bursts frames threshold
int main(int argc, char * argv[]) {
    // default process 1200000 frames (1 minute)
    // sleep(600+15);

    int frames = 10*60*20000;
    float threshold = 0.2;

    char *configPath = argv[1];
    ElectrodeMap emap = ElectrodeMap(configPath);
    
    if (argc >= 3) {
        frames = stoi(argv[2]);
    } if (argc >= 4) {
        threshold = stof(argv[3]);
    }

    std::fstream file;
    std::fstream alldata_file;
    file.open("side_test.csv", std::fstream::out);
    alldata_file.open("side_test_alldata.csv", std::fstream::out);

    // activate interrupt handler
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
    int burstStart = 0;
    int burstEnd = 0;
    int noSpikeFrameCount = 0;
    int spikeCount = 0;
    int lastSpike = 0;
    int blanking = 0;
    vector<float> locs;
    vector <int> burst_spikeCounts;
    locs.resize(10);
    burst_spikeCounts.resize(10);
    int capacity = 10;
    int loc_counter = 0;
    
    float monitoring_loc = 0;

    int startingLocDiff = 0; //not used anymore?
    vector<int> spikeCountWindow;
    vector<const SpikeEvent *> spikeEventWindow;
    cout << "Initial vector size: " << spikeCountWindow.size() << endl;
    cout << "Processing " << framesToSeconds(frames) / 60 << " minutes of neuron activity with a spike threshold of " << threshold << endl;


    // initialize the vector with 200 frames
    for (int i = 0; i < WINDOW; i++) {
        maxlab::FilteredFrameData frameData;
        maxlab::Status status = maxlab::DataStreamerFiltered_receiveNextFrame(&frameData);

        if (status == maxlab::Status::MAXLAB_NO_FRAME) {
            i--;
            continue;
        }
        spikeCount += frameData.spikeCount;

        spikeCountWindow.push_back(frameData.spikeCount);
        spikeEventWindow.push_back(frameData.spikeEvents);
    }


    // start processing frames
    for (int i = 0; i < frames; i++) {
        maxlab::FilteredFrameData frameData;
        maxlab::Status status = maxlab::DataStreamerFiltered_receiveNextFrame(&frameData);

        // If no data was read in, try again (happens when loop finishes before 
        // the machine takes another sample)
        if (status == maxlab::Status::MAXLAB_NO_FRAME) {
            i--;
            continue;
        }

        // const SpikeEvent *spike = frameData.spikeEvents;

        int oldSpikeCount = spikeCountWindow[0];

        spikeCountWindow.erase(spikeCountWindow.begin());
        spikeEventWindow.erase(spikeEventWindow.begin());
        
        spikeCount -= oldSpikeCount; 
        spikeCount += frameData.spikeCount;

        spikeCountWindow.push_back(frameData.spikeCount);
        spikeEventWindow.push_back(frameData.spikeEvents);

        if (blanking > 0) {
            blanking--;
            if (blanking != 0) {
                continue;
            }
        }

        if (i % (int)(FRAMES_PER_SEC * 0.01) == 0){
            monitoring_loc = get_avg_side(spikeEventWindow, spikeCountWindow, emap);
            alldata_file << i + SYS_START_BUFFER + WINDOW << ", " << spikeCount << ", " << monitoring_loc << endl;
        }
   
        if ((i == burstStart + (FRAMES_PER_SEC * 0.01 * loc_counter)) && loc_counter < capacity){
            locs[loc_counter] = get_avg_side(spikeEventWindow, spikeCountWindow, emap);
            burst_spikeCounts[loc_counter] = spikeCount;
            loc_counter++;
        }
        
        if  (spikeCount > threshold * TOTAL_ELECTRODES) {
            if (noSpikeFrameCount > 0 && spikeFrameCount == 0) {
                // cout << "_____________________________" << endl;
                // cout << i << ": Buffer lasting " << noSpikeFrameCount << " frames" << endl;
                // print_starting_location(spikeEventWindow, spikeCountWindow);
                locs[0] = get_avg_side(spikeEventWindow, spikeCountWindow, emap);
                burst_spikeCounts[0] = spikeCount;
                loc_counter = 1;
                //startingLocDiff = get_side_diff(spikeEventWindow, spikeCountWindow);
                burstStart = i;
            }
            
            spikeFrameCount++; // spike at this frame
            noSpikeFrameCount = 0;
        } else {
            // cout << (spikeWindowCount) << " vs " << (threshold * TOTAL_ELECTRODES) << endl;

            if (noSpikeFrameCount > 200) {
                if (spikeFrameCount >= MIN_FRAMES) {
                    burstEnd = i-200;
                    
                    // cout << "^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^" << endl;
                    // float seconds = framesToSeconds(spikeFrameCount);
                    // cout << "Detected burst lasting " << seconds << " seconds (" << spikeFrameCount << " frames), starting at position " << startingLoc << endl;

                    // // edge case: startingLocDiff = 0 (right for now)
                    int left = locs[0] < locs[capacity - 1];
                    string loc_string = left ? "left to right" : "right to left";
                    // int numSide = startingLocDiff * (left ? -1 : 1);
                    file <<"BURST" << endl;
                    file << burstStart + SYS_START_BUFFER + WINDOW << ", " << burstEnd + SYS_START_BUFFER + WINDOW << ", ";
                    
                    for(int m = 0; m < capacity; m++){
                        file << locs[m] << ", ";
                    }

                    file << loc_string << endl << ", ,";
                    for(int m = 0; m < capacity; m++){
                        file << burst_spikeCounts[m] << ", ";
                    }
                    
                    file << endl;



                    // cout << numSide << " extra spikes on the " << loc << " side" << endl;
                    // // print_starting_location(spikeEventWindow, spikeCountWindow);
                    // if (!left) {
                    //     maxlab::verifyStatus(maxlab::sendSequence("stim_seq"));
                    //     cout << i << ": sent stimulation after burst of " << seconds << " seconds (" << spikeFrameCount << " frames)" << endl;
                    //     blanking = 8000;
                    // }
                    
                }      
                spikeFrameCount = 0;
            }
            noSpikeFrameCount++;
        }
    } 

    cout << "program over  " << endl;
    maxlab::verifyStatus(maxlab::DataStreamerFiltered_close());
    file.close();
    alldata_file.close();

    return 0;
}

/* get_avg_side
 * 
 * Returns the average starting column of the spike events in a given window
 * 
 * Parameters:
 *      spikeEvents: window (vector) of SpikeEvent structs
 *      spikeCounts: vector (mirroring spikeEvents) of the number of spikes in 
 *                   the corresponding spikeEvent
 *  
 */
float get_avg_side(vector<const SpikeEvent *> spikeEvents, vector<int> spikeCounts, ElectrodeMap emap) {
    float sum = 0;
    float count = 0;
    for (int i = 0; i < spikeEvents.size(); i++) {
        const SpikeEvent *event = spikeEvents[i];
        // if (spikeCounts[i] > 0) {
        //     cout << "-------------------------------------------------" << endl;
        //     cout << "processing spike events from one frame:" << endl;
        // }
        
        for (int j = 0; j < spikeCounts[i]; j++) {
            // compute column coordinate and add to sum
            cout << "adding spike event from well " << (int) event[j].wellId << " and frame " << event[j].frameNo << endl;
            electrodeCoords coords = emap.get(event[j].channel);
            sum += coords.x;
            // cout << "Got spike from channel: " << coords.position << ": " << coords.position << "(" << coords.x << ", " << coords.y << ")" << endl;
            count++;
        }
        // if (spikeCounts[i] > 0) {
        //     cout << "-------------------------------------------------" << endl;
        // }
    }

    return sum / count;
}

/* get_side_diff
 * 
 * Returns the difference of the number of spikes on the left side of the chip 
 * and the right side of the chip. A positive integer indicates more spikes on 
 * the left side, and a positive integer indicates more spikes on the right.
 * 
 * Parameters:
 *      spikeEvents: window (vector) of SpikeEvent structs
 *      spikeCounts: vector (mirroring spikeEvents) of the number of spikes 
 *                   in the corresponding spikeEvent
 *  
 */
int get_side_diff(vector<const SpikeEvent *> spikeEvents, vector<int> spikeCounts) {
    int middle = CHIP_WIDTH / 2;
    int result = 0;
    for (int i = 0; i < spikeEvents.size(); i++) {

        const SpikeEvent *event = spikeEvents[i];

        for (int j = 0; j < spikeCounts[i]; j++) {
            int location = event[j].channel % CHIP_WIDTH; 

            // add one if on the left, subtract one if on the right
            result += (location < middle) ? -1 : 1;
        }
    }

    return result;
}

float framesToSeconds(int frames) {
    float seconds = (float) frames / (float) FRAMES_PER_SEC;
    return seconds;
}