/**
 * @file random-stim-test.cpp
 * @author Trevor Sullivan (trevor.sullivan@tufts.edu)
 * @brief This program randomly stimulates the chip every _ seconds, as 
 * done in new-train-wave.cpp. This program tests that logic and is intended 
 * to be called by stim_removal_wave.py
 * @version 0.1
 * @date 2024-11-07
 * 
 * @copyright Copyright (c) 2024
 * 
 */

#include <stdlib.h>
#include <stdio.h>
#include <iostream>
#include <unistd.h>
#include <algorithm>
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
using namespace argparse;


// amount of time to wait for system startup
//#define FRAMES_PER_SEC 10000
#define RANDOM_SEED 10
#define SYS_START_BUFFER 5 * FRAMES_PER_SEC
#define TOTAL_ELECTRODES emap.size()
#define MIN_FRAMES 0.1 * FRAMES_PER_SEC
#define WINDOW 0.01 * FRAMES_PER_SEC
#define CHIP_WIDTH 220  //87
#define CHIP_HEIGHT 120

#define THRESHOLD_DEFAULT WINDOW/1000
#define FRAMES_DEFAULT 15 * 60 * 20000
#define MINUTES_DEFAULT 15

#define STIM_RATE_DEFAULT 5 // stims per second
#define RANDOM_WINDOW_GEN_TIME 5 //5 seconds

#define USAGE "bruh"


int FRAMES_PER_SEC = 20000;

float framesToSeconds(int frames);
void runExperiment(string path, string configPath, int frames, float threshold, int well, int pollingWindowSize, int numPollingWindows, int numStims);
int getMaxElement(vector<int> v);


vector<int> generateRandomStim(int length, int numStims);

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
    srand(1);
 
    string folderPath = getStringArg("--folder", argc, argv, USAGE);
    string configPath = getStringArg("--config", argc, argv, USAGE);
    float threshold = getFloatArgSecure("--threshold", THRESHOLD_DEFAULT, argc, argv);
    bool maxtwo = checkOption("--maxtwo", argc, argv);
    int well = getIntArgSecure("--well", 0, argc, argv);

    // WHEN WORKING ON SETUP, CHANGE "_" to "-" for stim rate and pulse duration
    float stimRate = getFloatArgSecure("--stim-rate", STIM_RATE_DEFAULT, argc, argv);
    float pulseDurationSecs = getFloatArgSecure("--pulse-duration", 0.0002, argc, argv);
    float minutes = getFloatArgSecure("--minutes", MINUTES_DEFAULT, argc, argv);

    cout << "Running experiment on Max" << (maxtwo ? "Two" : "One") << " for " << minutes << " minutes..." << endl;
    cout << "Config: " << configPath << endl;
    cout << "Threshold: " << threshold << endl;
    cout << "Well: " << well << endl;
    ElectrodeMap emap = ElectrodeMap(configPath.c_str());
    
    if (maxtwo) {
        FRAMES_PER_SEC = 10000;
    }

    int frames = minutes * 60 * FRAMES_PER_SEC;
    
    int pulseDuration = pulseDurationSecs * FRAMES_PER_SEC;
    int pollingRate = 1000; //1000 per sec
    int pollingWindowSize = FRAMES_PER_SEC / pollingRate; //1 ms
    int numPollingWindows = pollingRate * RANDOM_WINDOW_GEN_TIME;
    int numStims = stimRate * RANDOM_WINDOW_GEN_TIME;
    //5000 discrete time bins in which stimuli can occur. These occur over 5 seconds

    if (pulseDuration * 2 > pollingWindowSize){
        cout << "pulse duration * 2 > polling window size" << endl;
        exit(2);
    }

    cout << "Frames per sec: " << FRAMES_PER_SEC << endl;
    cout << "Min frames: " << MIN_FRAMES << endl;

    try {
        runExperiment(folderPath, configPath, frames, threshold, well, pollingWindowSize, numPollingWindows, numStims);
    } catch (int err) {
        cout << "Program failed with error code " << err << endl;
        maxlab::verifyStatus(maxlab::DataStreamerFiltered_close());
        return err;
    }

    return 0;
}


void runExperiment(string path, string configPath, int frames, float threshold, int well, int pollingWindowSize, int numPollingWindows, int numStims) {
    // Open data stream and check that no errors occurred
    maxlab::verifyStatus(maxlab::DataStreamerFiltered_open(maxlab::FilterType::IIR));

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
    bool maxtwo = (FRAMES_PER_SEC == 10000);
    StimVector stimVector = StimVector(false, 5, maxtwo);

    // amount of blanking time
    int blanking = 0;    

    bool stimulate = false;

    string stimName = "pulse" + to_string(well);

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
        stimulate = stimVector.stimulate(i);
        

        if (blanking > 0) {
            blanking--;
        }

        //STIMULATE IF APPROPRIATE
        if (stimulate){
            maxlab::verifyStatus(maxlab::sendSequence(stimName.c_str()));
            cout << i << ": PULSE SENT" << endl;
            blanking = pollingWindowSize;
        }
    } 

    cout << "program over  " << endl;
    maxlab::verifyStatus(maxlab::DataStreamerFiltered_close());
}


float framesToSeconds(int frames) {
    float seconds = (float) frames / (float) FRAMES_PER_SEC;
    return seconds;
}

int getMaxElement(vector<int> v) {
    int maxVal = INT_MIN;
    for(int i = 0; i < v.size(); i++) {
        maxVal = max(v[i], maxVal);
    }
    return maxVal;
}