#include <stdlib.h>
#include <stdio.h>
#include <iostream>
#include <unistd.h>
// #include "maxlab.h"
#include <signal.h>
#include <vector>
#include <unistd.h>
#include <fstream>
#include <assert.h>
#include <limits.h>
#include "hal.h"
#include <map>

using namespace std;
using namespace maxlab;

// 220 x 120

// amount of time to wait for system startup
//#define FRAMES_PER_SEC 10000

#define SYS_START_BUFFER 5 * FRAMES_PER_SEC
#define TOTAL_ELECTRODES emap.size()
#define MIN_FRAMES 0.1 * FRAMES_PER_SEC
#define WINDOW 0.01 * FRAMES_PER_SEC
#define CHIP_WIDTH 220  //87
#define CHIP_HEIGHT 120

int FRAMES_PER_SEC = 20000;

float get_avg_side(ChannelWindow window);
float framesToSeconds(int frames);
void runExperiment(ElectrodeMap emap, int frames, float threshold, int well);
int get_max_element(vector<int> v);


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
    char *configPath = argv[1];
    ElectrodeMap emap = ElectrodeMap(configPath);
    int well = 0;
    
    if(argc >= 3 && stoi(argv[2])) {
        FRAMES_PER_SEC = 10000;
    }

    if(argc >= 4) {
        well = stoi(argv[3]);
    }

    
    int frames = 1*60*FRAMES_PER_SEC;
    
    float threshold = WINDOW/1000;

    cout << "Frames per sec: " << FRAMES_PER_SEC << endl;
    cout << "Min frames: " << MIN_FRAMES << endl;

    

    if (argc >= 5) {
        frames = stoi(argv[4]);
    } if (argc >= 6) {
        threshold = stof(argv[5]);
    }
    try {
        runExperiment(emap, frames, threshold, well);
    } catch (int err) {
        cout << "Program failed with error code " << err << endl;
        maxlab::verifyStatus(maxlab::DataStreamerFiltered_close());
        return err;
    }

    return 0;
}


void runExperiment(ElectrodeMap emap, int frames, float threshold, int well) {
    // Open data stream and check that no errors occurred
    maxlab::verifyStatus(maxlab::DataStreamerFiltered_open(maxlab::FilterType::IIR));

    std::fstream file;
    std::fstream alldata_file;
    std::fstream rawdata_file;
    file.open("data/side_test_" + to_string(well) + ".csv", std::fstream::out);
    alldata_file.open("data/side_test_alldata" + to_string(well) + ".csv", std::fstream::out);

    // activate interrupt handler
    signal(SIGINT, signal_interrupt_handler);

    // start up causes a lot of spikes
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

    // the number of frames where the spike count goes over the threshold
    int spikeFrameCount = 0;

    ChannelWindow window = ChannelWindow(WINDOW, emap);
    

    // frame number representing the start of a burst
    int burstStart = 0;

    // frame number representing the end of a burst 
    int burstEnd = 0;

    /* the number of frames since the last frame where the spike count went over
       the threshold */ 
    int noSpikeFrameCount = 0;

    // amount of blanking time
    int blanking = 0;

    // stores calculated average side at certain frames
    vector<float> locs(5);

    // spike count for each calculated location, mirroring locs
    vector <int> burstSpikeCounts(5);

    // number of locs that can be stored
    int capacity = 5;

    // number of locs that are currently being stored
    int locCounter = 0;
    
    float monitoringLoc = 0;

    // stores data for each frame in a 200-frame window
    vector<FilteredFrameData> frameWindow;
    cout << "Processing " << framesToSeconds(frames) / 60.0 << " minutes of neuron activity with a spike threshold of " << threshold << endl;


    // initialize the vector with 200 frames
    for (int i = 0; i < window.length(); i++) {
        maxlab::FilteredFrameData frameData;
        maxlab::Status status = maxlab::DataStreamerFiltered_receiveNextFrame(&frameData);

        if (status == maxlab::Status::MAXLAB_NO_FRAME) {
            i--;
            continue;
        }

        window.add(frameData);
    }

    bool switched = true;

    int switchCount = 0;
    // start processing frames
    for (int i = 0; i < frames; i++) {
        if (i == 0){
            maxlab::verifyStatus(maxlab::sendSequence("before-training"));
            cout << i << ": before training" << endl;

        } else if (i == frames/2) {
            maxlab::Response r = maxlab::sendRaw("system_set_primary_well 5");
            cout << i << ": Switched wells with status " << r.status;
            if (r.content != nullptr) {
                cout << ": \n\t" << r.content << endl;
            }
            switched = false;
        }
        else if (i == (int)((float)(frames)/3)) {
            maxlab::verifyStatus(maxlab::sendSequence("training"));
            cout << i << ": training" << endl;
        }
        else if (i == (int)((float)(2*frames)/3)) {
            maxlab::verifyStatus(maxlab::sendSequence("after-training"));
            cout << i << ": after training" << endl;
        }

        maxlab::FilteredFrameData frameData;
        maxlab::Status status = maxlab::DataStreamerFiltered_receiveNextFrame(&frameData);

        // If no data was read in, try again (happens when loop finishes before 
        // the machine takes another sample)
        if (status == maxlab::Status::MAXLAB_NO_FRAME) {
            i--;
            // if (!switched) {
            //     // cout << i << ": Switched, but no frame detected" << endl;
            //     switchCount++;
            // }
            continue;
        }

        if (!switched) {
            switchCount++;
            if (frameData.spikeCount == 0) {
                
                cout << switchCount << ": spike count is 0 " << well << endl;
            } else {
                int well = frameData.spikeEvents[0].wellId;
                if (well == 5) {
                    cout << i << ": successfully switched to well 5 after " << switchCount << " frames." << endl;
                    switched = true;
                } else {
                    cout << switchCount << ": still on well " << well << endl;
                }
            }
        }

        // const SpikeEvent *spike = frameData.spikeEvents;
        window.shift(frameData);
        int spikeCount = window.totalSpikeCount();


        if (blanking > 0) {
            blanking--;
            if (blanking != 0) {
                continue;
            }
        }

        if (i % (int)(FRAMES_PER_SEC * 0.01) == 0){
            monitoringLoc = get_avg_side(window);
            alldata_file << i + SYS_START_BUFFER + WINDOW << ", " << spikeCount << ", " << monitoringLoc << endl;
        }
   
        if ((i == burstStart + (FRAMES_PER_SEC * 0.01 * locCounter)) && locCounter < capacity){
            locs[locCounter] = get_avg_side(window);
            burstSpikeCounts[locCounter] = spikeCount;
            locCounter++;
        }
        
        // if the current spike count is over the threshold
        if  (spikeCount > threshold * TOTAL_ELECTRODES) {

            // start of the burst
            if (noSpikeFrameCount > 0 && spikeFrameCount == 0) { 
                locs[0] = get_avg_side(window); // starting location
                burstSpikeCounts[0] = spikeCount;
                locCounter = 1;
                burstStart = i;
            }
            
            spikeFrameCount++; // spike at this frame
            noSpikeFrameCount = 0;
        } else {

            // burst is over
            if (noSpikeFrameCount > 0.2 * FRAMES_PER_SEC) {

                // burst is long enough to be significant
                if (spikeFrameCount >= MIN_FRAMES) {
                    burstEnd = i-200;
                    
                    // // edge case: startingLocDiff = 0 (right for now)
                    int left = locs[0] < locs[capacity - 1];
                    string loc_string = left ? "left to right" : "right to left";
                    file <<"BURST" << endl;
                    file << burstStart + SYS_START_BUFFER + WINDOW << ", " << burstEnd + SYS_START_BUFFER + WINDOW << ", ";
                    
                    for(int m = 0; m < capacity; m++) {
                        file << locs[m] << ", ";
                    }

                    file << loc_string << endl << ", ,";
                    for(int m = 0; m < capacity; m++) {
                        file << burstSpikeCounts[m] << ", ";
                    }
                    
                    file << endl;

                    //left to right stimulation
                    //If in training phase
                    // if (i >= (int)((float)(frames)/3) && i < (int)((float)(2*frames)/3)) {
                        // if (left) {
                        //     maxlab::verifyStatus(maxlab::sendSequence("Left-to-Right"));
                        //     cout << i << ": sent left-to-right stimulation" << endl;
                        // } 
                        // else {
                        //     maxlab::verifyStatus(maxlab::sendSequence("Right-to-Left"));
                        //     cout << i << ": sent right-to-left stimulation" << endl;
                        // }

                        // blanking = 0.4 * FRAMES_PER_SEC;
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
}


/* get_avg_side
 * 
 * Returns the average starting column of the spike events in a given window
 * 
 * Parameters:
 *      frameWindow: vector of FilteredFrameData structs, representing a 
 *                   200-frame window of frame data
 *  
 */
float get_avg_side(ChannelWindow window) {
    ElectrodeMap emap = window.electrodeMap();

    // used to make sure that each channel is only counted once
    int channels[1024] = {0};
    float sum = 0;
    float count = 0;
    for (int i = 0; i < window.length(); i++) {
        FilteredFrameData fd = window.get(i);
        const SpikeEvent *event = fd.spikeEvents;
        int spikeCount = fd.spikeCount;
        for (int j = 0; j < spikeCount; j++) {
            // compute column coordinate and add to sum
            int channel = event[j].channel;
            // if the channel has already been counted
            if (channel < 1024 && channels[channel] == 0){
                if(channel > 1024){
                    cout << "ERROR WITH CHANNEL NUMBER- TOO HIGH" << endl;
                }
                float x_coord = emap.get_x(channel);
                if(x_coord < 0){ //channel number not found in the emap
                    // cout << "channel number " << channel << " fired, but is not in the channel mapping" << endl;
                }
                else{
                    sum += x_coord;
                    channels[channel] = 1;
                    count++;
                }

            }
            
        }
    }
    return sum / count;
}

float framesToSeconds(int frames) {
    float seconds = (float) frames / (float) FRAMES_PER_SEC;
    return seconds;
}

int get_max_element(vector<int> v){
    int maxVal = INT_MIN;
    for(int i = 0; i < v.size(); i++){
        maxVal = max(v[i], maxVal);
    }
    return maxVal;
}