#include <stdlib.h>
#include <stdio.h>
#include <iostream>
#include <unistd.h>
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
#include <algorithm>

#include <zmq.hpp>
#include <thread>
#include <chrono>


using namespace std;
using namespace maxlab;
using namespace argparse;

#define SYS_START_BUFFER 5 * FRAMES_PER_SEC
#define WINDOW 0.01 * FRAMES_PER_SEC

#define USAGE "Usage: ./control --config0 <config_path>  --config1 <config_path> --folder <folder_path>\n\n\
Options:\n\
\t[--maxtwo]             Indicates running on the MaxTwo\n\
\t[--minutes <value>]    Number of minutes to run, float (default 0.5)\n\
\t[--well <value>]       Well number, int (default 0)\n"

#define FRAMES_DEFAULT 15*60*20000
#define MINUTES_DEFAULT 15

int FRAMES_PER_SEC = 20000;
float rates[11] = {0.1, 0.2, 0.4, 0.8, 1.6, 3.2, 6.4, 7, 8, 9, 10};
std::vector<int> inc_idx = {0, 100000, 200000, 300000, 400000, 500000, 600000, 700000, 800000, 900000};
std::vector<int> dec_idx = {1000000, 1100000, 1200000, 1300000, 1400000, 1500000, 1600000, 1700000, 1800000, 1900000};


float get_avg_side(ChannelWindow window);
float framesToSeconds(int frames);
void runExperiment(string path, string config0, string config1, int frames, int well, bool guidance);
int get_max_element(vector<int> v);
void printUsage();
struct args getArgs(int argc, char *argv[]);
void printValues(fstream *data, string ab, int frameNo, float aRatioThreshold, float bRatioThreshold, float ratio, float valA, float avgA, float sdA, float valB, float avgB, float sdB);
float fanoFactor(float A, float B);
bool withinSD(float levels, float avg, float sd, float value);
float zScore(float value, float avg, float sd);

void sync() {
    // initialize the zmq context with a single IO thread
    zmq::context_t context{1};

    // construct a REQ (request) socket and connect to interface
    zmq::socket_t socket{context, zmq::socket_type::req};
    socket.connect("tcp://localhost:5556");

    // set up some static data to send
    const std::string data{"sync"};

    // send the request message
    std::cout << "Sending sync..." << std::endl;
    socket.send(zmq::buffer(data), zmq::send_flags::none);
    
    // wait for reply from server
    zmq::message_t reply{};
    socket.recv(reply, zmq::recv_flags::none);

    std::cout << "Received " << reply.to_string(); 
    std::cout << std::endl;
}

/* signal_interrupt_handler
 * 
 * Closes the DataStreamer when ^C is signalled.
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
    bool maxtwo = checkOption("--maxtwo", argc, argv);
    string path = getStringArg("--folder", argc, argv, USAGE);
    string config0 = getStringArg("--config0", argc, argv, USAGE);
    string config1 = getStringArg("--config1", argc, argv, USAGE);

    float minutes = getFloatArgSecure("--minutes", 0.5, argc, argv);
    int well = getIntArgSecure("--well", 0, argc, argv);
    bool guidance = checkOption("--guidance", argc, argv);
    cout << "Running experiment on Max" << (maxtwo ? "Two" : "One") << " for " << minutes << " minutes..." << endl;
    cout << "Well: " << well << endl;

    if (guidance){
        cout << "running with guidance" << endl;
    }
        
    if (maxtwo) {
        FRAMES_PER_SEC = 10000;
    }
    
    int frames = minutes*60*FRAMES_PER_SEC;

    try {
        runExperiment(path, config0, config1, frames, well, guidance);
    } catch (int err) {
        cout << "Program failed with error code " << err << endl;
        maxlab::verifyStatus(maxlab::DataStreamerFiltered_close());
        return err;
    }

    return 0;
}

void runExperiment(string path, string config0, string config1, int frames, int well, bool guidance) {
    // Open data stream and check that no errors occurred
    maxlab::verifyStatus(maxlab::DataStreamerFiltered_open(maxlab::FilterType::IIR));
    int stim_type = 0;

    int windowLength = 200;

    std::fstream data;
    std::fstream stim_tracker;
    data.open(path + "/store" + to_string(well) + ".csv", std::fstream::out);
    data << "frame number,button pressed,A ratio threshold,B ratio threshold,fano,value A,avg A,SD A,value B,avg B,SD B" << endl;
    stim_tracker.open(path + "/stim" + to_string(well) + ".csv", std::fstream::out);

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

    int blanking = 0;

    controller.addButton("A", windowLength, config0.c_str(), 9); //slow button
    controller.addButton("B", windowLength, config1.c_str(), 9); //fast button
    
    cout << "Processing " << framesToSeconds(frames) / 60.0 << " minutes of neuron activity" << endl;

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
    int numRatioFrames = FRAMES_PER_SEC * 1 * 60 ;
    ProgressBar ratioProgress = ProgressBar(numRatioFrames, "Calculating ratio thresholds...");

    /*
        Calibrate ratio thresholds
    */
    for (int i = 0; i < numRatioFrames; i++) {
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


        //TODO: check this
        if (winA->pastWindowsReady() && winB->pastWindowsReady()) {
            float firingRateAvgA = winA->avgPastWindows();
            float firingRateAvgB = winB->avgPastWindows();
            float sdA = winA->firingRateSD();
            float sdB = winB->firingRateSD();
            float firingRateA = winA->firingRate();
            float firingRateB = winB->firingRate();
            float fano = fanoFactor(firingRateAvgA, firingRateAvgB);

            if (firingRateA > 1 || firingRateB > 1) {
                ratios.push_back(fano);
            }
        }
    }
    cout << endl;

    sort(ratios.begin(), ratios.end());

    int numRatios = ratios.size() - 1;

    int aRatioIndex = 0.9 * numRatios;
    int bRatioIndex = 0.1 * numRatios;

    // float aRatio = 0.5;
    // float bRatio = -0.5;

    float aRatio = ratios[aRatioIndex];
    float bRatio = ratios[bRatioIndex];

    cout << "A Ratio Threshold: " << aRatio << endl;
    cout << "B Ratio Threshold: " << bRatio << endl;

    cout << "A Ratio Index: " << aRatioIndex << endl;
    cout << "B Ratio Index: " << bRatioIndex << endl;

    int framesPerMin = FRAMES_PER_SEC * 60;

    ProgressBar expBar = ProgressBar(frames, "Frequency game running...", true);

    bool aReleased = true;
    bool bReleased = true;

    int minStimRate = 200000; 
    int maxStimRate = 2250;

    int stimAcc = 19775; // how much the stim rate changes, in frames

    // how often the culture is stimulated, in frames
    int stimRate = minStimRate; 

    // initialize the zmq context with a single IO thread
    zmq::context_t context{1};

    // construct a REQ (request) socket and connect to interface
    zmq::socket_t socket{context, ZMQ_PUB};
    cout << "connecting..." << endl;
    socket.bind("tcp://*:5555");
    
    // set up some static data to send
    sync();

    cout << "Sockets initialized and synced" << endl;
    // const std::string data{"Hello"};

    const std::string stop{"stop"};

    /*
        Run Experiment
    */
    for (int i = 0; i < frames; i++) {
        maxlab::FilteredFrameData frameData;
        maxlab::Status status = maxlab::DataStreamerFiltered_receiveNextFrame(&frameData);


        // every minute
        if (i % framesPerMin == 0) {
            sort(ratios.begin(), ratios.end());

            numRatios = ratios.size() - 1;

            aRatioIndex = 0.9 * numRatios;
            bRatioIndex = 0.1 * numRatios;

            aRatio = ratios[aRatioIndex];
            bRatio = ratios[bRatioIndex];
            
            expBar.clear();
            cout << "New A Threshold: " << aRatio << endl;
            cout << "New B Threshold: " << bRatio << endl;
            expBar.print();
        }
        

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

        if (!blanking){
            controller.shift(frameData);
        }


        //TODO: check this
        if (winA->pastWindowsReady() && winB->pastWindowsReady() && (guidance == false) && !blanking) {
            float firingRateAvgA = winA->avgPastWindows();
            float firingRateAvgB = winB->avgPastWindows();
            float sdA = winA->firingRateSD();
            float sdB = winB->firingRateSD();
            float firingRateA = winA->firingRate();
            float firingRateB = winB->firingRate();
            float fano = fanoFactor(firingRateAvgA, firingRateAvgB);


            // Button A was pressed !withinSD(3, firingRateAvgA, sdA, firingRateA)
            if (aReleased && (firingRateAvgA != 0) && (firingRateA > 0.5) && (fano > aRatio) && (zScore(firingRateA, firingRateAvgA, sdA) > 2)) {

                printValues(&data, "A", i, aRatio, bRatio, fano, firingRateA, firingRateAvgA, sdA, firingRateB, firingRateAvgB, sdB);
                if (stimRate < minStimRate) {
                    stimRate += stimAcc;
                    stim_type--;
                }

                expBar.clear();
                cout << i << ": button A pressed " << stim_type << " " << int(FRAMES_PER_SEC * 2/rates[stim_type]) << endl;
                expBar.print();
               
                aReleased = false;
                float stimulationRate = FRAMES_PER_SEC / (float) stimRate;

                string data = "A;" + to_string(i / (float)FRAMES_PER_SEC) + ";" +  to_string(stim_type) + ";" + stimulationRate;
                // send the request message
                socket.send(zmq::buffer(data));

            // Button B was pressed zScore(firingRateB, firingRateAvgB, sdB) > 3
            } else if (bReleased && (firingRateAvgB != 0) && (firingRateB > 0.5) && (fano < bRatio) && (zScore(firingRateB, firingRateAvgB, sdB) > 2)) {
                
                printValues(&data, "B", i, aRatio, bRatio, fano, firingRateA, firingRateAvgA, sdA, firingRateB, firingRateAvgB, sdB);
                if (stimRate > maxStimRate) {
                    stimRate -= stimAcc;
                    stim_type++;
                }

                expBar.clear();
                cout << i << ": button B pressed " << stim_type << " " << int(FRAMES_PER_SEC * 2/rates[stim_type])<< endl;
                expBar.print();

                float stimulationRate = FRAMES_PER_SEC / (float) stimRate;

                bReleased = false;

                string data = "B;" + to_string(i / (float)FRAMES_PER_SEC) + ";" +  to_string(stim_type) + ";" + stimulationRate;
                // send the request message
                socket.send(zmq::buffer(data));
            } else {
                aReleased = true;
                bReleased = true;
            }

            if (firingRateA > 1 || firingRateB > 1) {
                ratios.push_back(fano);
            } 
        }

        float numSeconds = (float) i / FRAMES_PER_SEC;

        //TODO: get guidance
        if(guidance){
            if (i % 10000 == 0) {
                cout << i << endl;
            }
            //starts at the very firts frame and inc every 10 sec
            if (std::find(inc_idx.begin(), inc_idx.end(), i) != inc_idx.end() ){
                if (stim_type < 10){
                    stim_type++;
                    cout << i << ": Speed increased by guidance" << endl;
                    maxlab::verifyStatus(maxlab::sendSequence("inc_guidance"));
                }
            }

            if (std::find(dec_idx.begin(), dec_idx.end(), i) != dec_idx.end()){
                if (stim_type > 0){
                    stim_type--;
                    cout << "Speed decreased by guidance" << endl;
                    maxlab::verifyStatus(maxlab::sendSequence("dec_guidance"));
                }
            }

            if ((i >= 1900000)){
                guidance = false;
            }
        }

        if (i % stimRate == 0) {
            maxlab::verifyStatus(maxlab::sendSequence("stim"));
            blanking=200;
        }      
              
    }

    socket.send(zmq::buffer(stop));

    cout << "program over  " << endl;
    maxlab::verifyStatus(maxlab::DataStreamerFiltered_close());
    data.close();
    stim_tracker.close();

} 

float fanoFactor(float A, float B) {
    if (A == 0 && B == 0) {
        return 0;
    } else {
        return (A - B) / (A + B);
    }
}

float zScore(float value, float avg, float sd) {
    return (value - avg) / sd;
}

bool withinSD(float levels, float avg, float sd, float value) {
    float upper = avg + (levels * sd);
    float lower = avg - (levels * sd);

    return (value <= upper);
}

void printValues(fstream *data, string ab, int frameNo, float aRatioThreshold, float bRatioThreshold,  float ratio, float valA, float avgA, float sdA, float valB, float avgB, float sdB) {
    *data << frameNo << "," << ab << ", " << aRatioThreshold << ", " << bRatioThreshold << ", " << ratio << ",";
    *data << valA << "," << avgA << "," << sdA << ",";
    *data << valB << "," << avgB << "," << sdB << endl;
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