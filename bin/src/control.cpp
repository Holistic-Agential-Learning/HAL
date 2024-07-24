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

#define USAGE "Usage: ./control --config0 <config_path>  --config1 <config_path> --folder <folder_path>\n\n\
Options:\n\
\t[--maxtwo]             Indicates running on the MaxTwo\n\
\t[--minutes <value>]    Number of minutes to run, float (default 0.5)\n\
\t[--well <value>]       Well number, int (default 0)\n"

#define THRESHOLD_DEFAULT WINDOW/1000
#define FRAMES_DEFAULT 15*60*20000
#define MINUTES_DEFAULT 15

int FRAMES_PER_SEC = 20000;

float get_avg_side(ChannelWindow window);
float framesToSeconds(int frames);
void runExperiment(string path, string config0, string config1, int frames, int well);
int get_max_element(vector<int> v);
void printAndStimulate(fstream data, string ab, float ratio, float firingRateA, float devA, float firingRateB, float devB);
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
    // default process 1200000 frames (1 minute)
    // sleep(600+15);
    bool maxtwo = checkOption("--maxtwo", argc, argv);
    string path = getStringArg("--folder", argc, argv, USAGE);
    string config0 = getStringArg("--config0", argc, argv, USAGE);
    string config1 = getStringArg("--config1", argc, argv, USAGE);

    float minutes = getFloatArgSecure("--minutes", 0.5, argc, argv);
    int well = getIntArgSecure("--well", 0, argc, argv);
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

    int windowLength = 200;

    std::fstream data;
    data.open(path + "/std_dev_test_" + to_string(well) + ".csv", std::fstream::out);

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
    // ChannelWindow window = ChannelWindow(200, config0.c_str(), 9);

    int blanking = 0;

    controller.addButton("A", windowLength, config0.c_str(), 9);
    controller.addButton("B", windowLength, config1.c_str(), 9);

    cout << "Finished buffer, looking for spikes..." << endl;
    
    cout << "Processing " << framesToSeconds(frames) / 60.0 << " minutes of neuron activity with" << endl;

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
        // window.shift(frameData);

        if (blanking > 0) {
            blanking--;
            if (blanking != 0) {
                continue;
            }
        }

        ////////////////////////////////////////////////////////////////////////
        ChannelWindow *winA = controller.getButtonWindow("A");

        if (winA->pastWindowsReady()) {
            //
            
            ChannelWindow *winB = controller.getButtonWindow("B");

            float firingRateA = winA->avgPastWindows();
            float firingRateB = winB->avgPastWindows();
            float devA = winA->stdDev();
            float devB = winB->stdDev();
            float ratio = firingRateA / firingRateB;
            // data << i << ": " << ratio << "," << winA->totalSpikeCount() << "," << winB->totalSpikeCount() << endl;
            if (ratio > 1.1) {
                printAndStimulate(data, "A", ratio, firingRateA, devA, firingRateB, devB);
                blanking = 10 + 10000;
            } else if (ratio < 0.9) {
                printAndStimulate(data, "B", ratio, firingRateA, devA, firingRateB, devB);
                blanking = 10 + 10000;
            } 
        }

        float numSeconds = (float) i / FRAMES_PER_SEC;
    } 

    cout << "program over  " << endl;
    maxlab::verifyStatus(maxlab::DataStreamerFiltered_close());
    data.close();
}

void printAndStimulate(fstream data, string ab, float ratio, float firingRateA, float devA, float firingRateB, float devB) {
    data << i << ": " << ab << ", " << ratio << "," << firingRateA << "," << devA << "," << firingRateB << "," << devB << endl;
    if (ab == "B") {
        std::random_device rd;
        std::mt19937 gen(rd());
        std::uniform_int_distribution<> dis(0, 999);
        int randomInt = dis(gen);
        std::string punish_no = std::to_string(randomInt);
        std::string final_punish = "punish" + punish_no;
        maxlab::verifyStatus(maxlab::sendSequence(final_punish.c_str()));
        //maxlab::verifyStatus(maxlab::sendSequence("Left-to-Right"));
    } else if (ab == "A") {
        maxlab::verifyStatus(maxlab::sendSequence("reward"));
    }
    
    
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