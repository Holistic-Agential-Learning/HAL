/**
 * @file plot-frequency-game.cpp
 * @author Trevor Sullivan (trevor.sullivan@tufts.edu)
 * @brief This program runs a closed-loop frequency game experiment, where 
 *        the neuron culture can press "buttons" to increase or decrease the 
 *        rate of stimulation. It uses ZMQ to send data to a plotter (written 
 *        in Python in /bin/setup/plot-frequency-game.py), which plots the 
 *        button presses in real time.
 * @version 0.1
 * @date 2024-08-23
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
void runExperiment(string path, string config0, string config1, int frames, int minFramesPerStim, int maxFramesPerStim, int well, bool guidance, float spikePercentThreshold);

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

void runExperiment(string path, string config0, string config1, int frames, int minFramesPerStim, int maxFramesPerStim,int well, bool guidance, float spikePercentThreshold) {
    // Open data stream and check that no errors occurred
    maxlab::verifyStatus(maxlab::DataStreamerFiltered_open(maxlab::FilterType::IIR));
    int stimType = 0;

    int windowLength = 1000;

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
    NES controller = NES(maxtwo, windowLength, config0.c_str(), config1.c_str(), (path + "/button_data_well_" + to_string(well) + ".csv").c_str());
    cout << "Initializing NES..." << endl;
    controller.init();

    int blanking = 0;

    ChannelWindow *winA = controller.getButtonWindow("A");
    ChannelWindow *winB = controller.getButtonWindow("B");

    int framesPerMin = FRAMES_PER_SEC * 60;

    ProgressBar expBar = ProgressBar(frames, "Frequency game running...");
    
    float minStimRate = FRAMES_PER_SEC / (float) maxFramesPerStim;
    float maxStimRate = FRAMES_PER_SEC / (float) minFramesPerStim;

    // number of steps to get from the min stim rate to max stim rate
    int numSteps = 10;

    // acceleration (the amount to increase/decrease the stim rate by)
    float acc = (maxStimRate - minStimRate) / numSteps;

    // how often the culture is stimulated, in frames
    float stimRate = minStimRate; 
    cout << "Starting plotter..." << endl;
    Plotter plot = Plotter();

    cout << "Syncing sockets..." << endl;
    plot.sync();

    cout << "Sockets initialized and synced" << endl;

    int framesPerStim = 200000;

    int guidanceRate = 100000;
    bool increase = true;

    bool aReleased = true;
    bool bReleased = true;

    maxlab::verifyStatus(maxlab::sendSequence(("closed_loop_start_" + to_string(well)).c_str()));

    float zScoreThreshold = 3;

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

        if (!blanking && !guidance) {
            if (pressed == 1) {
                // Button A was pressed
                if (stimRate > minStimRate) {
                    stimRate -= acc;
                    stimType--;
                    framesPerStim = (1 / stimRate) * FRAMES_PER_SEC;
                }

                expBar.clear();
                cout << i << ": button A pressed " << stimType << " " << stimRate << endl;
                expBar.print();
            
                maxlab::verifyStatus(maxlab::sendSequence("A-pressed"));

                plot.sendFrequencyGameData("A", i / (float) FRAMES_PER_SEC, stimType, stimRate);
            } else if (pressed == 2) {
                // Button B was pressed
                if (stimRate < maxStimRate) {
                    stimRate += acc;
                    stimType++;
                    framesPerStim = (1 / stimRate) * FRAMES_PER_SEC;
                }

                expBar.clear();
                cout << i << ": button B pressed " << stimType << " " << stimRate << endl;
                expBar.print();

                maxlab::verifyStatus(maxlab::sendSequence("B-pressed"));

                plot.sendFrequencyGameData("B", i / (float) FRAMES_PER_SEC, stimType, stimRate);
            }
        }

        float numSeconds = (float) i / FRAMES_PER_SEC;

        // Guidance system -- simulates the frequency game by stimulating the buttons
        if(guidance) {
            //starts at the very firts frame and inc every 10 sec
            if (increase && i % guidanceRate == 0 && i != 0) {
                if (stimRate < maxStimRate) {
                    stimRate += acc;
                    stimType++;
                    framesPerStim = (1 / stimRate) * FRAMES_PER_SEC;
                    expBar.clear();
                    cout << i << ": Speed increased by guidance" << endl;
                    cout << stimRate << ", " << framesPerStim << endl;
                    expBar.print();
                    maxlab::verifyStatus(maxlab::sendSequence("inc_guidance"));
                    
                    // send to plotter for testing 
                    plot.sendFrequencyGameData("B", i / (float) FRAMES_PER_SEC, stimType, stimRate);
                } else {
                    increase = false;
                }
            } else if (!increase && i % guidanceRate == 0) {
                if (stimRate > minStimRate) {
                    stimRate -= acc;
                    stimType--;
                    framesPerStim = (1 / stimRate) * FRAMES_PER_SEC;
                    expBar.clear();
                    cout << i << ": Speed decreased by guidance" << endl;
                    cout << stimRate << ", " << framesPerStim << endl;
                    expBar.print();
                    maxlab::verifyStatus(maxlab::sendSequence("dec_guidance"));

                    plot.sendFrequencyGameData("A", i / (float) FRAMES_PER_SEC, stimType, stimRate);
                } if (stimRate == minStimRate) {
                    guidance = false;
                }
            }
        }

        if (i % framesPerStim == 0) {
            // expBar.clear();
            // cout << i << ": stimulation sent" << endl;
            // expBar.print();

            // data << i << ": stimulation sent" << endl;
            maxlab::verifyStatus(maxlab::sendSequence("stim"));
            blanking=500;
        }
              
    }
    // tell plotter that the program is over
    plot.close();

    cout << "program over - starting post recording " << endl;
    maxlab::verifyStatus(maxlab::DataStreamerFiltered_close());
} 

// run with ./prints-bursts frames threshold
int main(int argc, char * argv[]) {
    // required arguments
    string path = getStringArg("--folder", argc, argv, USAGE);
    string config0 = getStringArg("--config0", argc, argv, USAGE);
    string config1 = getStringArg("--config1", argc, argv, USAGE);

    // optional arguments
    bool maxtwo = checkOption("--maxtwo", argc, argv);
    float minutes = getFloatArgSecure("--minutes", 0.5, argc, argv);
    int well = getIntArgSecure("--well", 0, argc, argv);
    bool guidance = checkOption("--guidance", argc, argv);

    int lower = getIntArgSecure("--lower", 5000, argc, argv);
    int upper = getIntArgSecure("--upper", 200000, argc, argv);

    float spikePercent = getFloatArgSecure("--spike-percent-thresh", 0.03, argc, argv);

    cout << "Running experiment on Max" << (maxtwo ? "Two" : "One");
    cout << " for " << minutes << " minutes on well " << well << endl;

    if (guidance) {
        cout << "Running with guidance system" << endl;
    }
        
    if (maxtwo) {
        FRAMES_PER_SEC = 10000;
    }
    
    int frames = minutes * 60 * FRAMES_PER_SEC;

    try {
        runExperiment(path, config0, config1, frames, lower, upper, well, guidance, spikePercent);
    } catch (int err) {
        cout << "Program failed with error code " << err << endl;
        maxlab::verifyStatus(maxlab::DataStreamerFiltered_close());
        return err;
    }

    return 0;
}
