/**
 * @file channel-window-test.cpp
 * @author Trevor Sullivan (trevor.sullivan@tufts.edu)
 * @brief Used to test ChannelWindow
 * @version 0.1
 * @date 2024-09-03
 * 
 * @copyright Copyright (c) 2024
 * 
 */

#include <stdlib.h>
#include <stdio.h>
#include <iostream>
#include <unistd.h>
#include <signal.h>
#include <vector>
#include <unistd.h>
#include <fstream>
#include <string>
#include "hal.h"
#include <algorithm>
#include <zmq.hpp>
#include <thread>
#include <chrono>

using namespace std;
using namespace maxlab;
using namespace argparse;

#define SYS_START_BUFFER 5 * FRAMES_PER_SEC
#define WINDOW 0.01 * FRAMES_PER_SEC

#define USAGE "Usage: ./plot-frequency-game --config0 <config_path>  --config1 <config_path> --folder <folder_path>\n\n\
Options:\n\
\t[--maxtwo]             Indicates running on the MaxTwo\n\
\t[--minutes <value>]    Number of minutes to run, float \n\
\t[--well <value>]       Well number, int (default 0)\n\
\t[--ratio-time <value>] Time to calculate button ratios before the experiment\
 begins.\n"

#define FRAMES_DEFAULT 15*60*20000
#define MINUTES_DEFAULT 15

int FRAMES_PER_SEC = 20000;

void runExperiment(string path, string config, int frames, int well);

void signal_interrupt_handler(int sig) {
    cout << " signalled!" << endl;
    maxlab::verifyStatus(maxlab::DataStreamerFiltered_close());
    exit(sig);
}

void printValues(fstream *data, string ab, int frameNo, float perA, float valA, float avgA, float sdA, float zA, float perB, float valB, float avgB, float sdB, float zB) {
    *data << frameNo << ", " << ab << ", " ;
    *data << perA << ", "<< valA << ", " << avgA << ", " << sdA << ", " << zA << ", ";
    *data << perB << ", "<< valB << ", " << avgB << ", " << sdB << ", " << zB << endl;
}


void runExperiment(string path, string config, int frames, int well) {
    // Open data stream and check that no errors occurred
    maxlab::verifyStatus(maxlab::DataStreamerFiltered_open(maxlab::FilterType::IIR));

    int windowLength = 1000;
    std::fstream thresholds;
    thresholds.open(path + "/thresholds_well_" + to_string(well) + ".txt", std::fstream::out);

    // activate interrupt handler
    signal(SIGINT, signal_interrupt_handler);

    // start up causes a lot of spikes, so skip over it
    for (int i = 0; i < SYS_START_BUFFER; i++) {
        maxlab::FilteredFrameData frameData;
        maxlab::Status status = maxlab::DataStreamerFiltered_receiveNextFrame(&frameData);
        if (status == maxlab::Status::MAXLAB_NO_FRAME) {
            i--;
            continue;
        }
    }

    bool maxtwo = FRAMES_PER_SEC == 10000;

    ChannelWindow window = ChannelWindow(windowLength, config.c_str());
    window.init();

    int framesPerMin = FRAMES_PER_SEC * 60;

    /*
        Run Experiment
    */
    for (int i = 0; i < frames; i++) {
        maxlab::FilteredFrameData frameData;
        maxlab::Status status = maxlab::DataStreamerFiltered_receiveNextFrame(&frameData);

        // If no data was read in, try again (happens when loop finishes before 
        // the machine takes another sample)
        if (status == maxlab::Status::MAXLAB_NO_FRAME) {
            i--;
            continue;
        }

        expBar.increment();

        // don't add data that includes stimulations
        controller.shift(frameData);

    }
    maxlab::verifyStatus(maxlab::DataStreamerFiltered_close());
} 

// run with ./prints-bursts frames threshold
int main(int argc, char * argv[]) {
    // required arguments
    string path = getStringArg("--folder", argc, argv, USAGE);
    string config = getStringArg("--config", argc, argv, USAGE);

    // optional arguments
    bool maxtwo = checkOption("--maxtwo", argc, argv);
    float minutes = getFloatArgSecure("--minutes", 0.5, argc, argv);
    int well = getIntArgSecure("--well", 0, argc, argv);

    cout << "Running experiment on Max" << (maxtwo ? "Two" : "One");
    cout << " for " << minutes << " minutes on well " << well << endl;
        
    if (maxtwo) {
        FRAMES_PER_SEC = 10000;
    }
    
    int frames = minutes * 60 * FRAMES_PER_SEC;
    int ratioFrames = ratioTime * 60 * FRAMES_PER_SEC;

    try {
        runExperiment(path, config, frames, well);
    } catch (int err) {
        cout << "Program failed with error code " << err << endl;
        maxlab::verifyStatus(maxlab::DataStreamerFiltered_close());
        return err;
    }

    return 0;
}
