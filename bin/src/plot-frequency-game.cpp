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

#define USAGE "Usage: \n\
  ./plot-frequency-game --config0 <file>  --config1 <file> --folder <path> \
(--stim-freq-file <file> | --stim-freqs <value>) [--maxtwo] [--guidance] \
[--minutes <value>] [--well <value>] [--spike-percent-thresh <value>]\n\n\
Options:\n\
  --config0 <file>                      Full path to configuration file for \
button A, string\n\
  --config1 <file>                      Full path to configuration file for \
button B, string\n\
  --folder <path>                       Full path to data folder created by \
the setup script, string\n\
  --stim-freq-file <value>              Full path to stimulation frequency \
file \n\
  --stim-freqs <value>                  Comma-separated stimulation \
frequencies in Hz, float\n\
  --maxtwo                              Indicates running on the MaxTwo\n\
  --guidance                            Run the guidance system at the \
beginning of the experiment\n\
  --minutes <value>                     Number of minutes to run, float \n\
  --well <value>                        Well number, int (default 0)\n\
  --spike-percent-thresh <value>        Percent of channels in a button that \
need to spike for a button press\n"

int FRAMES_PER_SEC = 20000;

// needs to be global to close connection in case of interrupt 
Plotter plot = Plotter();

// void runExperiment(string path, string config0, string config1, int frames, int minFramesPerStim, int maxFramesPerStim, int well, bool guidance, float spikePercentThreshold);

void signal_interrupt_handler(int sig) {
    cout << " signalled!" << endl;
    maxlab::verifyStatus(maxlab::DataStreamerFiltered_close());
    plot.close();
    exit(sig);
}

// grabs floats from string, comma separated
vector<float> parseFloats(string floatList) {
    size_t startIdx = 0;
    size_t target = 0;
    vector<float> freqs;
    while ((target = floatList.find(",", startIdx)) != string::npos) {
        string value = floatList.substr(startIdx, target);
        startIdx = target + 1;
        freqs.push_back(stof(value.c_str()));
    } 

    freqs.push_back(stof(floatList.substr(startIdx, target).c_str()));

    return freqs;

}

// gets list of frequencies from either
vector<float> getFrequencies(int argc, char *argv[]) {
    bool isFile = checkOption("--stim-freq-file", argc, argv);
    string freqString = "";

    if (isFile) {
        // read from file
        string freqFile = getStringArg("--stim-freq-file", argc, argv);
        ifstream file;

        file.open(freqFile.c_str());
        if (!file.is_open()) {
            cerr << "Error: failed to open " << freqFile << endl;
            exit(1);
        }

        getline(file, freqString);

    } else {
        // from the command line or nonexistent
        freqString = getStringArg("--stim-freqs", argc, argv, USAGE);
    }

    return parseFloats(freqString);
}



void runExperiment(string path, string config0, string config1, vector<float> frequencies, int frames, int well, bool guidance, float spikePercentThreshold) {
    // Open data stream and check that no errors occurred
    maxlab::verifyStatus(maxlab::DataStreamerFiltered_open(maxlab::FilterType::IIR));
    int level = 0;
    int maxLevel = frequencies.size() - 1;
    float stimRate = frequencies[level];
    int framesPerStim = (1 / stimRate) * FRAMES_PER_SEC;

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
    NES controller = NES(FRAMES_PER_SEC == 10000, windowLength, config0.c_str(), config1.c_str(), (path + "/button_data_well_" + to_string(well) + ".csv").c_str());
    cout << "Initializing NES..." << endl;
    controller.init();

    int blanking = 0;

    int framesPerMin = FRAMES_PER_SEC * 60;

    ProgressBar expBar = ProgressBar(frames, "Frequency game running...");

    cout << "Starting plotter..." << endl;
    // plot = Plotter();

    cout << "Syncing sockets..." << endl;
    plot.sync();

    cout << "Sockets initialized and synced" << endl;

    int guidanceRate = 100000;
    bool increase = true;

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

        if (!blanking && !guidance) {
            if (pressed == 1) {
                // Button A was pressed
                if (level > 0) {
                    level--;
                    stimRate = frequencies[level];
                    framesPerStim = (1 / stimRate) * FRAMES_PER_SEC;
                }

                expBar.clear();
                cout << i << ": button A pressed " << level << " " << stimRate << endl;
                expBar.print();
            
                maxlab::verifyStatus(maxlab::sendSequence("A-pressed"));

                plot.sendFrequencyGameData("A", i / (float) FRAMES_PER_SEC, level, stimRate);
            } else if (pressed == 2) {
                // Button B was pressed
                if (level < maxLevel) {
                    level++;
                    stimRate = frequencies[level];
                    framesPerStim = (1 / stimRate) * FRAMES_PER_SEC;
                }

                expBar.clear();
                cout << i << ": button B pressed " << level << " " << stimRate << endl;
                expBar.print();

                maxlab::verifyStatus(maxlab::sendSequence("B-pressed"));

                plot.sendFrequencyGameData("B", i / (float) FRAMES_PER_SEC, level, stimRate);
            }
        }

        float numSeconds = (float) i / FRAMES_PER_SEC;

        // Guidance system -- simulates the frequency game by stimulating the buttons
        if(guidance) {
            //starts at the very firts frame and inc every 10 sec
            if (increase && i % guidanceRate == 0 && i != 0) {
                if (level < maxLevel) {
                    level++;
                    stimRate = frequencies[level];
                    framesPerStim = (1 / stimRate) * FRAMES_PER_SEC;
                    expBar.clear();
                    cout << i << ": Speed increased by guidance" << endl;
                    cout << stimRate << ", " << framesPerStim << endl;
                    expBar.print();
                    maxlab::verifyStatus(maxlab::sendSequence("inc_guidance"));
                    
                    // send to plotter for testing 
                    plot.sendFrequencyGameData("B", i / (float) FRAMES_PER_SEC, level, stimRate);
                } else {
                    increase = false;
                }
            } else if (!increase && i % guidanceRate == 0) {
                if (level > 0) {
                    level--;
                    stimRate = frequencies[level];
                    framesPerStim = (1 / stimRate) * FRAMES_PER_SEC;
                    expBar.clear();
                    cout << i << ": Speed decreased by guidance" << endl;
                    cout << stimRate << ", " << framesPerStim << endl;
                    expBar.print();
                    maxlab::verifyStatus(maxlab::sendSequence("dec_guidance"));

                    plot.sendFrequencyGameData("A", i / (float) FRAMES_PER_SEC, level, stimRate);
                } if (stimRate == 0) {
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

    vector<float> freqs = getFrequencies(argc, argv);

    // optional arguments
    bool maxtwo = checkOption("--maxtwo", argc, argv);
    float minutes = getFloatArgSecure("--minutes", 0.5, argc, argv);
    int well = getIntArgSecure("--well", 0, argc, argv);
    bool guidance = checkOption("--guidance", argc, argv);

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
        runExperiment(path, config0, config1, freqs, frames, well, guidance, spikePercent);
    } catch (int err) {
        cout << "Program failed with error code " << err << endl;
        maxlab::verifyStatus(maxlab::DataStreamerFiltered_close());
        return err;
    }

    return 0;
}
