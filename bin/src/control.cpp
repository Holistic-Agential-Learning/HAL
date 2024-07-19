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
#include <random>
#include <string>
#include "hal.h"
#include <map>

using namespace std;
using namespace maxlab;

#define SYS_START_BUFFER 5 * FRAMES_PER_SEC
#define TOTAL_ELECTRODES emap.size()
#define MIN_FRAMES 0.1 * FRAMES_PER_SEC
#define WINDOW 0.01 * FRAMES_PER_SEC
#define CHIP_WIDTH 220  //87
#define CHIP_HEIGHT 120

#define USAGE "Usage: ./train-wave-direction --config <config_path> \n\n\
Options:\n\
\t[--maxtwo]             Indicates running on the MaxTwo\n\
\t[--threshold <value>]  Threshold for burst detection (must be a decimal between 0 and 1)\n\
\t[--minutes <value>]     Number of minutes to run\n\
\t[--well <value>]       Well number\n"

#define THRESHOLD_DEFAULT WINDOW/1000
#define FRAMES_DEFAULT 15*60*20000
#define MINUTES_DEFAULT 15

int FRAMES_PER_SEC = 20000;

struct args {
    bool maxtwo;
    string config_path;
    float threshold;
    int minutes;
    int well;
    string path;
};

float get_avg_side(ChannelWindow window);
float framesToSeconds(int frames);
void runExperiment(string path, string config0, string config1, int frames, int well);
int get_max_element(vector<int> v);
void printUsage();
struct args getArgs(int argc, char *argv[]);

void printUsage() {
    cout << USAGE << endl;
}

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

/*
    args:
        --config0 <path> --config1 <path> --folder <path>
*/

// run with ./prints-bursts frames threshold
int main(int argc, char * argv[]) {
    // default process 1200000 frames (1 minute)
    // sleep(600+15);
    // struct args params = getArgs(argc, argv);
    bool maxtwo = checkOption("--maxtwo", argc, argv);
    string path = getStringArg("--folder", argc, argv);
    string config0 = getStringArg("--config0", argc, argv);
    string config1 = getStringArg("--config0", argc, argv);

    float minutes = getFloatArgSecure("--minutes", argc, argv, 3);
    int well = getIntArgSecure("--well", argc, argv, 0);
    cout << "Running experiment on Max" << (maxtwo ? "Two" : "One") << " for " << minutes << " minutes..." << endl;
    cout << "Well: " << well << endl;
        
    if (maxtwo) {
        FRAMES_PER_SEC = 10000;
    }
    
    int frames = minutes*60*FRAMES_PER_SEC;

    try {
        runExperiment(path, config0, config1, frames, well);
    } catch (int err) {
        cout << "Program failed with error code " << err << endl;
        maxlab::verifyStatus(maxlab::DataStreamerFiltered_close());
        return err;
    }

    return 0;
}


void runExperiment(string path, string config0, string config1, int frames, int well) {
    // Open data stream and check that no errors occurred
    maxlab::verifyStatus(maxlab::DataStreamerFiltered_open(maxlab::FilterType::IIR));

    int windowLength = 10000;

    std::fstream file;
    std::fstream alldata_file;
    std::fstream rawdata_file;
    file.open(path + "/burst_direction_" + to_string(well) + ".csv", std::fstream::out);
    alldata_file.open(path + "/alldata_" + to_string(well) + ".csv", std::fstream::out);

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

    Controller controller = Controller();

    controller.addButton(config0, "A", windowLength);
    controller.addButton(config1, "B", windowLength);

    cout << "Finished buffer, looking for spikes..." << endl;
    
    cout << "Processing " << framesToSeconds(frames) / 60.0 << " minutes of neuron activity with a spike threshold of " << threshold << endl;

    // initialize the vector with 200 frames
    for (int i = 0; i < windowLength; i++) {
        maxlab::FilteredFrameData frameData;
        maxlab::Status status = maxlab::DataStreamerFiltered_receiveNextFrame(&frameData);

        if (status == maxlab::Status::MAXLAB_NO_FRAME) {
            i--;
            continue;
        }

        controller.add(frameData);
    }

    cout << "Finished controller initialization" << endl;


    // start processing frames
    for (int i = 0; i < frames; i++) {
        if (i == 0){
            maxlab::verifyStatus(maxlab::sendSequence("before-training"));
            cout << i << ": before training" << endl;

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
            continue;
        }

        // const SpikeEvent *spike = frameData.spikeEvents;
        controller.shift(frameData);

        if (blanking > 0) {
            blanking--;
            if (blanking != 0) {
                continue;
            }
        }

        

        ////////////////////////////////////////////////////////////////////////

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
                    if (i >= (int)((float)(frames)/3) && i < (int)((float)(2*frames)/3)) {
                        //if (i < (int)((float)(2*frames)/3)) {
                        if (!left) {
                            std::random_device rd;
                            std::mt19937 gen(rd());
                            std::uniform_int_distribution<> dis(0, 999);
                            int randomInt = dis(gen);
                            std::string punish_no = std::to_string(randomInt);
                            std::string final_punish = "punish" + punish_no;
                            cout << final_punish << endl;
                            maxlab::verifyStatus(maxlab::sendSequence(final_punish.c_str()));
                            //maxlab::verifyStatus(maxlab::sendSequence("Left-to-Right"));
                            cout << i << ": punish stimulation" << endl;
                        } 
                        else {
                            //maxlab::verifyStatus(maxlab::sendSequence("Right-to-Left"));
                            maxlab::verifyStatus(maxlab::sendSequence("reward"));
                            cout << i << ": sent reward stimulation" << endl;

                        }

                        blanking = 3*FRAMES_PER_SEC;
                    }
                    
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