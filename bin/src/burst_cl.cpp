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

float get_avg_side(ChannelWindow window);
float framesToSeconds(int frames);
void runExperiment(string path, string config0, string config1, int frames, int well);
int get_max_element(vector<int> v);
void printUsage();
struct args getArgs(int argc, char *argv[]);
void printValues(fstream *data, string ab, int frameNo, float ratio, float valA, float avgA, float sdA, float valB, float avgB, float sdB);
float fanoFactor(float A, float B);
bool withinSD(float levels, float avg, float sd, float value);
float zScore(float value, float avg, float sd);

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
    int stim_type = 0;

    int windowLength = 200;

    std::fstream data;
    std::fstream stim_tracker;
    data.open(path + "/store" + to_string(well) + ".csv", std::fstream::out);
    data << "frame number,button,fano,value A,avg A,SD A,value B,avg B,SD B" << endl;
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
    // ChannelWindow window = ChannelWindow(200, config0.c_str(), 9);

    int blanking = 0;

    controller.addButton("A", windowLength, config0.c_str(), 9); //slow button
    controller.addButton("B", windowLength, config1.c_str(), 9); //fast button

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

    ChannelWindow *winA = controller.getButtonWindow("A");
    ChannelWindow *winB = controller.getButtonWindow("B");



    for (int i = 0; i < frames; i++) {
        maxlab::FilteredFrameData frameData;
        maxlab::Status status = maxlab::DataStreamerFiltered_receiveNextFrame(&frameData);
        

        // If no data was read in, try again (happens when loop finishes before 
        // the machine takes another sample)
        if (status == maxlab::Status::MAXLAB_NO_FRAME) {
            i--;
            continue;
        }


        stim_tracker << stim_type << endl;
        
        controller.shift(frameData);

        if (blanking > 0) {
            blanking--;
            if (blanking != 0) {
                continue;
            }
        }


        //TODO: check this
        if (winA->pastWindowsReady() && winB->pastWindowsReady()) {
            float firingRateAvgA = winA->avgPastWindows();
            float firingRateAvgB = winB->avgPastWindows();
            float sdA = winA->firingRateSD();
            float sdB = winB->firingRateSD();
            float firingRateA = winA->firingRate();
            float firingRateB = winB->firingRate();
            float fano = fanoFactor(firingRateAvgA, firingRateAvgB);

             
            if (zScore(firingRateB, firingRateAvgB, sdB) > 2 && zScore(firingRateB, firingRateAvgB, sdB) > 2){
                //if both A & B are pressed, ignore both
            } else {
                // Button A was pressed !withinSD(3, firingRateAvgA, sdA, firingRateA)
                if (firingRateAvgA != 0 && firingRateA > 0.5 && fano > 0.5 && zScore(firingRateA, firingRateAvgA, sdA) > 2) {

                    printValues(&data, "A", i, fano, firingRateA, firingRateAvgA, sdA, firingRateB, firingRateAvgB, sdB);
                    if (stim_type > 0){
                        stim_type--;
                    }

                    cout << "btnA pressed" << endl;
                    
    
                // Button B was pressed zScore(firingRateB, firingRateAvgB, sdB) > 3
                } else if (firingRateAvgB != 0 && firingRateB > 0.5 && fano < -0.5 && zScore(firingRateB, firingRateAvgB, sdB) > 2) {
                    
                    printValues(&data, "B", i, fano, firingRateA, firingRateAvgA, sdA, firingRateB, firingRateAvgB, sdB);
                    if (stim_type < 10){
                        stim_type++;
                    }

                    cout << "btnB pressed" << endl;
                }    
            }

            
        }

        float numSeconds = (float) i / FRAMES_PER_SEC;

         switch(stim_type) {
            case 0:
                if (i % int(FRAMES_PER_SEC * 1/0.1) == 0) {
                    data << i << ": Pressing stim..." << endl;
                    cout << "Pressing stim" << endl;
                    maxlab::verifyStatus(maxlab::sendSequence("stim"));
                    blanking=200;
                }
               
                break;
            case 1:
                if (i % int(FRAMES_PER_SEC * 1/1) == 0) {
                   data << i << ": Pressing stim..." << endl;
                    cout << "Pressing stim" << endl;
                    maxlab::verifyStatus(maxlab::sendSequence("stim"));
                    blanking=200;
                }
                break;
            case 2:
                if (i % int(FRAMES_PER_SEC * 1/2) == 0) {
                    data << i << ": Pressing A..." << endl;
                    cout << "Pressing A" << endl;
                   maxlab::verifyStatus(maxlab::sendSequence("stim"));
                   blanking=200;
                }
                 
                break;
            case 3:
               if (i % int(FRAMES_PER_SEC * 1/3) == 0) {
                    data << i << ": Pressing stim..." << endl;
                    cout << "Pressing stim" << endl;
                    maxlab::verifyStatus(maxlab::sendSequence("stim"));
                    blanking=200;
                }
                 
                break;
            case 4:
                if (i % int(FRAMES_PER_SEC * 1/4) == 0) {
                     data << i << ": Pressing stim..." << endl;
                    cout << "Pressing stim" << endl;
                    maxlab::verifyStatus(maxlab::sendSequence("stim"));
                    blanking=200;
                }
                 
                break;
            case 5:
                if (i % int(FRAMES_PER_SEC * 1/5) == 0) {
                    data << i << ": Pressing stim..." << endl;
                    cout << "Pressing stim" << endl;
                    maxlab::verifyStatus(maxlab::sendSequence("stim"));
                    blanking=200;
                }
                 
                break;
            case 6:
                if (i % int(FRAMES_PER_SEC * 1/6) == 0) {
                     data << i << ": Pressing stim..." << endl;
                    cout << "Pressing stim" << endl;
                    maxlab::verifyStatus(maxlab::sendSequence("stim"));
                    blanking=200;
                }
                 
                break;
            case 7:
               if (i % int(FRAMES_PER_SEC * 1/7) == 0) {
                    data << i << ": Pressing stim..." << endl;
                    cout << "Pressing stim" << endl;
                    maxlab::verifyStatus(maxlab::sendSequence("stim"));
                    blanking=200;
                }
                
                break;
            case 8:
                if (i % int(FRAMES_PER_SEC * 1/8) == 0) {
                    data << i << ": Pressing A..." << endl;
                    cout << "Pressing A" << endl;
                    maxlab::verifyStatus(maxlab::sendSequence("stim"));
                    blanking=200;
                }
                break;
            case 9:
                if (i % int(FRAMES_PER_SEC * 1/9) == 0) {
                    data << i << ": Pressing stim..." << endl;
                    cout << "Pressing stim" << endl;
                    maxlab::verifyStatus(maxlab::sendSequence("stim"));
                    blanking=200;
                }
                break;
            case 10:
                if (i % int(FRAMES_PER_SEC * 1/10) == 0) {
                    data << i << ": Pressing stim..." << endl;
                    cout << "Pressing stim" << endl;
                    maxlab::verifyStatus(maxlab::sendSequence("stim"));
                    blanking=200;
                }
                break;
            default:
                cout << "incorrect stim type, nothing delivered";
            }
    }

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

void printValues(fstream *data, string ab, int frameNo, float ratio, float valA, float avgA, float sdA, float valB, float avgB, float sdB) {
    *data << frameNo << "," << ab << ", " << ratio << ",";
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