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
float calcRatio(float A, float B);
float zScore(float value, float avg, float sd);
void runExperiment(string path, string config0, string config1, int frames, int ratioFrames, int minFramesPerStim, int maxFramesPerStim, int well, bool guidance, float spikePercentThreshold);

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


void runExperiment(string path, string config0, string config1, int frames, int ratioFrames, int minFramesPerStim, int maxFramesPerStim,int well, bool guidance, float spikePercentThreshold) {
    // Open data stream and check that no errors occurred
    maxlab::verifyStatus(maxlab::DataStreamerFiltered_open(maxlab::FilterType::IIR));
    int stimType = 0;

    int windowLength = 1000;

    std::fstream data;
    data.open(path + "/button_data_well_" + to_string(well) + ".csv", std::fstream::out);
    data << "frame number, button pressed, percent fired A, firing rate A, avg FR A, SD A, Z score A, percent fired B, firing rate B, avg FR B, SD B, Z Score B" << endl;

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
    
    ProgressBar controllerProgress = ProgressBar(windowLength, "Initializing controller...");

    // initialize the vector with 200 frames
    for (int i = 0; i < windowLength; i++) {
        maxlab::FilteredFrameData frameData;
        maxlab::Status status = maxlab::DataStreamerFiltered_receiveNextFrame(&frameData);

        if (status == maxlab::Status::MAXLAB_NO_FRAME) {
            i--;
            continue;
        }

        controller.add(frameData);
        controllerProgress.increment();
    }
    cout << endl;

    ChannelWindow *winA = controller.getButtonWindow("A");
    ChannelWindow *winB = controller.getButtonWindow("B");

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

    int framesPerMin = FRAMES_PER_SEC * 60;

    ProgressBar expBar = ProgressBar(frames, "Frequency game running...");
    
    float minStimRate = FRAMES_PER_SEC / (float) maxFramesPerStim;
    float maxStimRate = FRAMES_PER_SEC / (float) minFramesPerStim;

    // cout << minStimRate << endl << maxStimRate << endl;

    // number of steps to get from the min stim rate to max stim rate
    int numSteps = 10;

    // acceleration (the amount to increase/decrease the stim rate by)
    float acc = (maxStimRate - minStimRate) / numSteps;
    // cout << acc << endl;

    // how often the culture is stimulated, in frames
    float stimRate = minStimRate; 
    cout << "starting plotter..." << endl;
    Plotter plot = Plotter();

    cout << "syncing..." << endl;
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


         bool pressed = false;
        // 0 indicates that no button was pressed
        string buttonPressed = "0";
       
        if (!guidance && winA->pastWindowsReady() && winB->pastWindowsReady() && !blanking) {
            float firingRateAvgA = winA->avgPastWindows();
            float firingRateAvgB = winB->avgPastWindows();
            float sdA = winA->firingRateSD();
            float sdB = winB->firingRateSD();
            float firingRateA = winA->firingRate();
            float firingRateB = winB->firingRate();
            float zScoreA = zScore(firingRateA, firingRateAvgA, sdA);
            float zScoreB = zScore(firingRateB, firingRateAvgB, sdB);
            int spikeCountA = winA->totalSpikeCount();
            int spikeCountB = winB->totalSpikeCount();

            int numChannelsA = winA->numChannels();
            int numChannelsB = winB->numChannels();

            float percentChannelsFiredA = spikeCountA / (float) numChannelsA;
            float percentChannelsFiredB = spikeCountB / (float) numChannelsB;

            bool aPressed = false;
            bool bPressed = false;

            // Button A was pressed
            if (aReleased && bReleased && zScoreA > zScoreThreshold && percentChannelsFiredA > spikePercentThreshold) {
                aPressed = true;
            // Button B was pressed 
            } else if (aReleased && bReleased && zScoreB > zScoreThreshold && percentChannelsFiredB > spikePercentThreshold) {
                bPressed = true;
            } 

            // check if the button is currently being "pressed"
            aReleased = !aPressed;
            bReleased = !bPressed;

            // ensure that only A or B gets pressed
            if (aPressed && bPressed) {
                if (percentChannelsFiredA >= percentChannelsFiredB) {
                    bPressed = false;
                } else aPressed = false;
            }

            // Button A was pressed
            if (aPressed) {
                buttonPressed = "1";

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

            // Button B was pressed 
            } else if (bPressed) {
                buttonPressed = "2";

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

            printValues(&data, buttonPressed, i, percentChannelsFiredA, firingRateA, firingRateAvgA, sdA, zScoreA, percentChannelsFiredB, firingRateB, firingRateAvgB, sdB, zScoreB);
        }

        float numSeconds = (float) i / FRAMES_PER_SEC;

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
    float minutes = getFloatArgSecure("--minutes", 0.5, argc, argv);
    float ratioTime = getFloatArgSecure("--ratio-time", 5, argc, argv);
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
    int ratioFrames = ratioTime * 60 * FRAMES_PER_SEC;

    try {
        runExperiment(path, config0, config1, frames, 0, lower, upper, well, guidance, spikePercent);
    } catch (int err) {
        cout << "Program failed with error code " << err << endl;
        maxlab::verifyStatus(maxlab::DataStreamerFiltered_close());
        return err;
    }

    return 0;
}
