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
void runExperiment(string path, string config0, string config1, int frames, int ratioFrames, int well, bool isLive, float spikePercentThreshold);

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

void printValues(fstream *data, string ab, int frameNo, float perA, float valA, float avgA, float sdA, float zA, float perB, float valB, float avgB, float sdB, float zB) {
    *data << frameNo << ", " << ab << ", " ;
    *data << perA << ", "<< valA << ", " << avgA << ", " << sdA << ", " << zA << ", ";
    *data << perB << ", "<< valB << ", " << avgB << ", " << sdB << ", " << zB << endl;
}


void runExperiment(string path, string config0, string config1, int frames, int ratioFrames, int well, bool isLive, float spikePercentThreshold) {
    // Open data stream and check that no errors occurred
    maxlab::verifyStatus(maxlab::DataStreamerFiltered_open(maxlab::FilterType::IIR));
    int stimType = 0;

    int windowLength = 1000;
    std::fstream thresholds;
    thresholds.open(path + "/thresholds_well_" + to_string(well) + ".txt", std::fstream::out);

    std::fstream data;
    data.open(path + "/button_data_well_" + to_string(well) + ".csv", std::fstream::out);
    data << "frame number, button pressed, percent fired A, firing rate A, avg FR A, SD A, Z score A, percent fired B, firing rate B, avg FR B, SD B, Z Score B" << endl;
    if (data.is_open()) {
        cout << "successfully opened data" << endl;
    }
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
    string csvName = path + "/button_data_well_" + to_string(well) + "_NES.csv";

    cout << "CSV: " << (path + "/button_data_well_" + to_string(well) + "_NES.csv").c_str() << endl;
    // initialize controller
    NES controller = NES(maxtwo, windowLength, config0.c_str(), config1.c_str(), (path + "/button_data_well_" + to_string(well) + "_NES.csv").c_str());

    int blanking = 0;

    // controller.addButton("A", windowLength, config0.c_str(), 50); //slow button
    // controller.addButton("B", windowLength, config1.c_str(), 50); //fast button
    
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

    ProgressBar expBar = ProgressBar(frames, "Button verification running...");

    maxlab::verifyStatus(maxlab::sendSequence(("closed_loop_start_" + to_string(well)).c_str()));

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

        int pressed = controller.checkButtons(i);

        if (pressed == 1) {
            maxlab::verifyStatus(maxlab::sendSequence("A-pressed"));

            expBar.clear();
            cout << i << ": button A pressed " << endl;
            expBar.print();
        } else if (pressed == 2) {
            maxlab::verifyStatus(maxlab::sendSequence("B-pressed"));

            expBar.clear();
            cout << i << ": button B pressed " << endl;
            expBar.print();
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
    thresholds.close();
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
    float spikePercent = getFloatArgSecure("--spike-percent-thresh", 0.03, argc, argv);


    cout << "Running experiment on Max" << (maxtwo ? "Two" : "One");
    cout << " for " << minutes << " minutes on well " << well << endl;
        
    if (maxtwo) {
        FRAMES_PER_SEC = 10000;
    }
    
    int frames = minutes * 60 * FRAMES_PER_SEC;
    int ratioFrames = ratioTime * 60 * FRAMES_PER_SEC;

    try {
        runExperiment(path, config0, config1, frames, 0, well, live, spikePercent);
    } catch (int err) {
        cout << "Program failed with error code " << err << endl;
        maxlab::verifyStatus(maxlab::DataStreamerFiltered_close());
        return err;
    }

    return 0;
}
