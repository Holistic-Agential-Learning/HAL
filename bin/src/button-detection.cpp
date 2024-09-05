/**
 * @file button-verification.cpp
 * @author Trevor Sullivan (trevor.sullivan@tufts.edu)
 * @brief This program verifies the methodology of button presses.
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

void sync();
float calcRatio(float A, float B);
float zScore(float value, float avg, float sd);
// void printValues(fstream *data, string ab, int frameNo, float ratio, float valA, float avgA, float zA, float valB, float avgB, float zB);
void runExperiment(string path, string config0, string config1, int frames, int ratioFrames, int well, bool isLive);

void signal_interrupt_handler(int sig) {
    cout << " signalled!" << endl;
    maxlab::verifyStatus(maxlab::DataStreamerFiltered_close());
    exit(sig);
}

/**
 * @brief Syncs with Python plotter 
 * 
 * 
 */
void sync() {
    zmq::context_t context{1};

    zmq::socket_t socket{context, zmq::socket_type::req};
    socket.connect("tcp://localhost:5556");

    const std::string data{"sync"};

    std::cout << "Sending sync..." << std::endl;
    socket.send(zmq::buffer(data), zmq::send_flags::none);
    
    zmq::message_t reply{};
    socket.recv(reply, zmq::recv_flags::none);

    std::cout << "Received " << reply.to_string(); 
    std::cout << std::endl;
}

float calcRatio(float A, float B) {
    if (A == 0 && B == 0) {
        return 0;
    } else {
        return (A - B) / (A + B);
    }
}

float zScore(float value, float avg, float sd) {
    return (value - avg) / sd;
}

void printValues(fstream *data, string ab, int frameNo, float ratio, float valA, float avgA, float sdA, float zA, float valB, float avgB, float sdB, float zB) {
    *data << frameNo << ", " << ab << ", " << ratio << ", ";
    *data << valA << ", " << avgA << ", " << sdA << ", " << zA << ", ";
    *data << valB << ", " << avgB << ", " << sdB << ", " << zB << endl;
}


void runExperiment(string path, string config0, string config1, int frames, int ratioFrames, int well, bool isLive) {
    // Open data stream and check that no errors occurred
    maxlab::verifyStatus(maxlab::DataStreamerFiltered_open(maxlab::FilterType::IIR));
    int stimType = 0;

    int windowLength = 200;

    std::fstream data;
    data.open(path + "/button_data_well_" + to_string(well) + ".csv", std::fstream::out);
    data << "frame number, button pressed, firing rate A, avg FR A, Z score A, firing rate B, avg FR B, Z Score B" << endl;

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
    
    // initialize controller
    Controller controller = Controller();

    int blanking = 0;

    controller.addButton("A", windowLength, config0.c_str(), 49); //slow button
    controller.addButton("B", windowLength, config1.c_str(), 49); //fast button
    
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

    ChannelWindow *winA = controller.getButtonWindow("A");
    ChannelWindow *winB = controller.getButtonWindow("B");

    int framesPerMin = FRAMES_PER_SEC * 60;

    vector<float> ratios;

    // amount of time to gather data for ratio threshold calculation
    ProgressBar ratioProgress = ProgressBar(ratioFrames, "Calculating ratio thresholds...");

    /*
        Calibrate ratio thresholds
    */
    for (int i = 0; i < ratioFrames; i++) {
        maxlab::FilteredFrameData frameData;
        maxlab::Status status = maxlab::DataStreamerFiltered_receiveNextFrame(&frameData);
        
        // If no data was read in, try again (happens when loop finishes before 
        // the machine takes another sample)
        if (status == maxlab::Status::MAXLAB_NO_FRAME) {
            i--;
            continue;
        }        
        controller.shift(frameData);
        ratioProgress.increment();

        if (winA->pastWindowsReady() && winB->pastWindowsReady()) {
            float firingRateAvgA = winA->avgPastWindows();
            float firingRateAvgB = winB->avgPastWindows();
            float firingRateA = winA->firingRate();
            float firingRateB = winB->firingRate();
            
            if (firingRateA > 0 && firingRateB > 0) {
                float ratio = calcRatio(firingRateAvgA, firingRateAvgB);
                ratios.push_back(ratio);
            }
        }
    }
    cout << endl;

    float aRatio;
    float bRatio;
    int aRatioIndex;
    int bRatioIndex;
    int numRatios;

    if (ratios.size() < 10) {
        aRatio = 0.5;
        bRatio = -0.5;
    } else {
        // sort all ratios
        sort(ratios.begin(), ratios.end());

        numRatios = ratios.size() - 1;

        // get 10th percentile and 90th percentile
        aRatioIndex = 0.9 * numRatios;
        bRatioIndex = 0.1 * numRatios;

        aRatio = ratios[aRatioIndex];
        bRatio = ratios[bRatioIndex];
    }

    ratios.clear();

    cout << "A Ratio Threshold: " << aRatio << endl;
    cout << "B Ratio Threshold: " << bRatio << endl;


    ProgressBar expBar = ProgressBar(frames, "Button verification running...");

    bool aReleased = true;
    bool bReleased = true;

    maxlab::verifyStatus(maxlab::sendSequence(("closed_loop_start_" + to_string(well)).c_str()));

    float zScoreThreshold = 6;

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

        if (blanking > 0) {
            blanking--;
        }

        if (!blanking) {
            controller.shift(frameData);
        }

        bool pressed = false;
       
        if (winA->pastWindowsReady() && winB->pastWindowsReady() && !blanking) {
            float firingRateAvgA = winA->avgPastWindows();
            float firingRateAvgB = winB->avgPastWindows();
            float sdA = winA->firingRateSD();
            float sdB = winB->firingRateSD();
            float firingRateA = winA->firingRate();
            float firingRateB = winB->firingRate();
            float zScoreA = zScore(firingRateA, firingRateAvgA, sdA);
            float zScoreB = zScore(firingRateB, firingRateAvgB, sdB);

            // get normalized difference
            float ratio = calcRatio(firingRateA, firingRateB);

            // Button A was pressed
            if (aReleased && firingRateAvgA != 0 && zScoreA > zScoreThreshold && zScoreA > zScoreB && ratio > aRatio) {
                printValues(&data, "A", i, ratio, firingRateA, firingRateAvgA, sdA, zScoreA, firingRateB, firingRateAvgB, sdB, zScoreB);

                expBar.clear();
                cout << i << ": button A pressed " << endl;
                expBar.print();

                maxlab::verifyStatus(maxlab::sendSequence("A-pressed"));

                pressed = true;
                
            // Button B was pressed 
            } else if (bReleased && firingRateAvgB != 0 && zScoreB > zScoreThreshold && zScoreB > zScoreA && ratio < bRatio) {
                printValues(&data, "B", i, ratio, firingRateA, firingRateAvgA, sdA, zScoreA, firingRateB, firingRateAvgB, sdB, zScoreB);

                expBar.clear();
                cout << i << ": button B pressed " << endl;
                expBar.print();

                maxlab::verifyStatus(maxlab::sendSequence("B-pressed"));

                pressed = true;
            } 

            aReleased = (zScoreA > zScoreThreshold) ? false : true;
            bReleased = (zScoreB > zScoreThreshold) ? false : true;

            if (!pressed) {
                // N indicates that no button was pressed
                printValues(&data, "N", i, firingRateA, firingRateAvgA, zScoreA, firingRateB, firingRateAvgB, zScoreB);
            }
        }

        if (!isLive) {
            // stimulate config A every second that's a multiple of 10
            if (i % (FRAMES_PER_SEC * 10) == 0) {
                data << i << ": Pressing A..." << endl;
                cout << "Pressing A" << endl;
                // maxlab::verifyStatus(maxlab::sendSequence("A"));

            // stimulation config B every second that's a multiple of 5 (but not 10)
            } else if (i % (FRAMES_PER_SEC * 5) == 0) {
                data << i << ": Pressing B..." << endl;
                cout << "Pressing B" << endl;
                // maxlab::verifyStatus(maxlab::sendSequence("B"));
            }
        }
    }
    maxlab::verifyStatus(maxlab::sendSequence(("end_experiment_" + to_string(well)).c_str()));
    cout << "program over - starting post recording " << endl;
    maxlab::verifyStatus(maxlab::DataStreamerFiltered_close());
    data.close();
} 

// run with ./prints-bursts frames threshold
int main(int argc, char * argv[]) {
    // required arguments
    string path = getStringArg("--folder", argc, argv, USAGE);
    string config0 = getStringArg("--config0", argc, argv, USAGE);
    string config1 = getStringArg("--config1", argc, argv, USAGE);

    // optional arguments
    bool maxtwo = checkOption("--maxtwo", argc, argv);
    bool live = checkOption("--live", argc, argv);
    float minutes = getFloatArgSecure("--minutes", 0.5, argc, argv);
    int well = getIntArgSecure("--well", 0, argc, argv);
    int ratioTime = getIntArgSecure("--ratio-time", 5, argc, argv);


    cout << "Running experiment on Max" << (maxtwo ? "Two" : "One");
    cout << " for " << minutes << " minutes on well " << well << endl;
        
    if (maxtwo) {
        FRAMES_PER_SEC = 10000;
    }
    
    int frames = minutes * 60 * FRAMES_PER_SEC;
    int ratioFrames = ratioTime * 60 * FRAMES_PER_SEC;

    try {
        runExperiment(path, config0, config1, frames, ratioFrames, well, live);
    } catch (int err) {
        cout << "Program failed with error code " << err << endl;
        maxlab::verifyStatus(maxlab::DataStreamerFiltered_close());
        return err;
    }

    return 0;
}
