/* raw-data-test.cpp
 *
 * This file serves as a test for the RawDataStreamer on the MaxTwo. When using 
 * the RawDataStreamer, it should get data frames from all active wells on the 
 * MaxTwo. This file tests to see 1) if that is true and 2) in what order does
 * that happen?
 * 
 * Run with:
 *  
 *      ./raw-data-test [--minutes <value>]
 * 
 * Where the value associated with the -minutes option is the amount of time 
 * that the experiment will run for. The default is 1.
 * 
 * Written by Trevor M. Sullivan
 * July 3, 2024
 */

#include <stdlib.h>
#include <stdio.h>
#include <iostream>
#include <unistd.h>
#include "maxlab.h"
#include <signal.h>
#include <vector>
#include <unistd.h>
#include <fstream>
#include <assert.h>
#include <limits.h>
#include "hal.h"
#include <map>

using namespace std;

#define SYS_START_BUFFER 5 * FRAMES_PER_SEC
#define TOTAL_ELECTRODES emap.size()
#define MIN_FRAMES 0.1 * FRAMES_PER_SEC
#define WINDOW 0.01 * FRAMES_PER_SEC
#define CHIP_WIDTH 220  //87
#define CHIP_HEIGHT 120

#define THRESHOLD_DEFAULT WINDOW/1000
#define FRAMES_DEFAULT 15*60*20000
#define MINUTES_DEFAULT 15

int FRAMES_PER_SEC = 10000;

float framesToSeconds(int frames);
void runExperiment(int frames);

/* signal_interrupt_handler
 * 
 * Closes the DataStreamer when ^c is signalled.
 * 
 */
void signal_interrupt_handler(int sig) {
    cout << " signalled!" << endl;
    maxlab::verifyStatus(maxlab::DataStreamerRaw_close());
    exit(sig);
}

// run with ./prints-bursts frames threshold
int main(int argc, char * argv[]) {
    // default process 1200000 frames (1 minute)
    // sleep(600+15);
    float minutes = getFloatArgSecure("--minutes", 1, argc, argv);
    
    int frames = minutes * 60 * FRAMES_PER_SEC;

    try {
        runExperiment(frames);
    } catch (int err) {
        cout << "Program failed with error code " << err << endl;
        maxlab::verifyStatus(maxlab::DataStreamerRaw_close());
        return err;
    }

    return 0;
}


void runExperiment(int frames) {
    // Open data stream and check that no errors occurred
    maxlab::verifyStatus(maxlab::DataStreamerRaw_open());

    std::fstream rawdata_file;
    rawdata_file.open("data/raw_data_test.csv", std::fstream::out);

    // activate interrupt handler
    signal(SIGINT, signal_interrupt_handler);

    // start up causes a lot of spikes
    // don't record the system startup stuff
    for (int i = 0; i < SYS_START_BUFFER; i++) {
        maxlab::RawFrameData frameData;
        maxlab::Status status = maxlab::DataStreamerRaw_receiveNextFrame(&frameData);
        if (status == maxlab::Status::MAXLAB_NO_FRAME) {
            i--;
            continue;
        }
    }
    cout << "Finished buffer, monitoring data..." << endl;

    // start processing frames
    for (int i = 0; i < frames; i++) {

        maxlab::RawFrameData frameData;
        maxlab::Status status = maxlab::DataStreamerRaw_receiveNextFrame(&frameData);

        // If no data was read in, try again (happens when loop finishes before 
        // the machine takes another sample)
        if (status == maxlab::Status::MAXLAB_NO_FRAME) {
            i--;
            continue;
        }

        maxlab::FrameInfo fi = frameData.frameInfo;
        int relativeFrame = i;
        int frame = fi.frame_number;
        int well = fi.well_id;
        bool corrupted = fi.corrupted;

        rawdata_file << relativeFrame << "," << frame << ",";
        rawdata_file << well << "," << corrupted << endl;
    } 

    cout << "program over  " << endl;
    maxlab::verifyStatus(maxlab::DataStreamerRaw_close());
    rawdata_file.close();
}

float framesToSeconds(int frames) {
    float seconds = (float) frames / (float) FRAMES_PER_SEC;
    return seconds;
}