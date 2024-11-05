#include <stdlib.h>
#include <stdio.h>
#include <iostream>
#include <unistd.h>
#include <algorithm>
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


//To generate a random sequence with a set firing rate, I shuffle 0s and 1s. 
    //How long are my stim pulses?
    //What is my smallest size of unit?
    //What is the average firing rate per electrode?

/*
Arguments:
    - frames
    - well
    - config path
    - threshold
    - maxtwo (int)

*/

/*

Usage: ./train-wave-direction --config <config_path> 

Options:
    [--maxtwo]             Indicates running on the MaxTwo          
    [--threshold <value>]  Threshold for burst detection (must be a decimal between 0 and 1)
    [--frames <value>]     Number of frames to run for
    [--well <value>]       Well number

*/

// 220 x 120

// amount of time to wait for system startup
//#define FRAMES_PER_SEC 10000
#define RANDOM_SEED 10
#define SYS_START_BUFFER 5 * FRAMES_PER_SEC
#define TOTAL_ELECTRODES emap.size()
#define MIN_FRAMES 0.1 * FRAMES_PER_SEC
#define WINDOW 0.01 * FRAMES_PER_SEC
#define CHIP_WIDTH 220  //87
#define CHIP_HEIGHT 120

#define USAGE "Usage: ./new-train-wave --config <file> --folder \
<path> [--maxtwo] [--pulse-duration <value>] [--threshold <value>] \
[--minutes <value>] [--well <value>]\n\n\
Options:\n\
\t--config <file>                 Full path to configuration file for \
experiment\n\
\t--folder <path>                 Full path to parent folder for saving data\n\
\t--maxtwo                        Indicates running on the MaxTwo\n\
\t--pulse-duration <value>        Duration of a single pulse, in second, \
default 0.0002\n\
\t--stim-rate <value>             Duration of a single pulse, in stimulations \
per second, default 5\n\
\t--threshold <value>             Threshold for burst detection, float between \
0 and 1, defalt (window length) / 1000\n\
\t--minutes <value>               Number of minutes to run the experiment, \
default 15\n\
\t--well <value>                  Well number, default 0\n"

#define THRESHOLD_DEFAULT WINDOW/1000
#define FRAMES_DEFAULT 15 * 60 * 20000
#define MINUTES_DEFAULT 15

#define STIM_RATE_DEFAULT 5 // stims per second
#define RANDOM_WINDOW_GEN_TIME 5 //5 seconds


int FRAMES_PER_SEC = 20000;

float framesToSeconds(int frames);
void runExperiment(string path, string configPath, int frames, float threshold, int well, int pollingWindowSize, int numPollingWindows, int num_stims);
int getMaxElement(vector<int> v);


vector<int> generateRandomStim(int length, int numStims);

/* signal_interrupt_handler
 * 
 * Closes the DataStreamer when ^c is signalled.
 * 
 */
void signal_interrupt_handler(int sig) {
    cout << " signalled!" << endl;
    maxlab::verifyStatus(maxlab::DataStreamerFiltered_close());
    exit(sig);
}

// run with ./prints-bursts frames threshold
int main(int argc, char * argv[]) {
    srand(1);
    cout << USAGE << endl;
    exit(1);
 
    string folderPath = getStringArg("--folder", argc, argv, USAGE);
    string configPath = getStringArg("--config", argc, argv, USAGE);
    float threshold = getFloatArgSecure("--threshold", THRESHOLD_DEFAULT, argc, argv);
    bool maxtwo = checkOption("--maxtwo", argc, argv);
    int well = getIntArgSecure("--well", 0, argc, argv);

    // WHEN WORKING ON SETUP, CHANGE "_" to "-" for stim rate and pulse duration
    float stimRate = getFloatArgSecure("--stim-rate", STIM_RATE_DEFAULT, argc, argv);
    float pulseDurationSecs = getFloatArgSecure("--pulse-duration", 0.0002, argc, argv);
    float minutes = getFloatArgSecure("--minutes", MINUTES_DEFAULT, argc, argv);

    cout << "Running experiment on Max" << (maxtwo ? "Two" : "One") << " for " << minutes << " minutes..." << endl;
    cout << "Config: " << configPath << endl;
    cout << "Threshold: " << threshold << endl;
    cout << "Well: " << well << endl;
    ElectrodeMap emap = ElectrodeMap(configPath.c_str());
    
    if (maxtwo) {
        FRAMES_PER_SEC = 10000;
    }

    int frames = minutes * 60 * FRAMES_PER_SEC;
    
    int pulseDuration = pulseDurationSecs * FRAMES_PER_SEC;
    int pollingRate = 1000; //1000 per sec
    int pollingWindowSize = FRAMES_PER_SEC / pollingRate; //1 ms
    int numPollingWindows = pollingRate * RANDOM_WINDOW_GEN_TIME;
    int numStims = stimRate * RANDOM_WINDOW_GEN_TIME;
    //5000 discrete time bins in which stimuli can occur. These occur over 5 seconds

    if (pulseDuration * 2 > pollingWindowSize){
        cout << "pulse duration * 2 > polling window size" << endl;
        exit(2);
    }

    cout << "Frames per sec: " << FRAMES_PER_SEC << endl;
    cout << "Min frames: " << MIN_FRAMES << endl;

    try {
        runExperiment(folderPath, configPath, frames, threshold, well, pollingWindowSize, numPollingWindows, numStims);
    } catch (int err) {
        cout << "Program failed with error code " << err << endl;
        maxlab::verifyStatus(maxlab::DataStreamerFiltered_close());
        return err;
    }

    return 0;
}


void runExperiment(string path, string configPath, int frames, float threshold, int well, int pollingWindowSize, int numPollingWindows, int num_stims) {
    // Open data stream and check that no errors occurred
    maxlab::verifyStatus(maxlab::DataStreamerFiltered_open(maxlab::FilterType::IIR));

    std::fstream file;
    std::fstream alldata_file;
    std::fstream rawdata_file;
    file.open(path + "/burst_direction_" + to_string(well) + ".csv", std::fstream::out);
    alldata_file.open(path + "/alldata_" + to_string(well) + ".csv", std::fstream::out);

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
    cout << "Finished buffer, looking for spikes..." << endl;
    vector <int> stimVector = generateRandomStim(numPollingWindows, num_stims);

    // amount of blanking time
    int blanking = 0;

    // number of locs that can be stored
    int capacity = 10; //1 second

    // stores calculated average side at certain frames
    vector<float> locs(capacity);

    // spike count for each calculated location, mirroring locs
    vector <int> burstSpikeCounts(capacity);
    
    bool training = false;
    bool stimulate = false;
    bool bursting = false;

    bool firstBurstDone = false;
    int maxSpikesFrame = 0;
    int maxSpikes = 0;
    float maxSpikesLoc = 0;

    // number of locs that are currently being stored
    int locCounter = 0;
    
    float monitoringLoc = 0;

    int previousBurstInDesiredDirection = 0;

    cout << "Processing " << framesToSeconds(frames) / 60.0 << " minutes of neuron activity with a spike threshold of " << threshold << endl;

    // gets wave detector object and initializes window
    WaveDetector sensor = WaveDetector(WINDOW, configPath.c_str(), threshold, MIN_FRAMES, FRAMES_PER_SEC, 0.2, 0.2);
    ChannelWindow *window = sensor.getWindow();

    // start processing frames
    for (int i = 0; i < frames; i++) {

        maxlab::FilteredFrameData frameData;
        maxlab::Status status = maxlab::DataStreamerFiltered_receiveNextFrame(&frameData);

        // If no data was read in, try again (happens when loop finishes before 
        // the machine takes another sample)
        if (status == maxlab::Status::MAXLAB_NO_FRAME) {
            i--;
            continue;
        }

        // const SpikeEvent *spike = frameData.spikeEvents;
        int waveVal = sensor.processFrame(frameData, i);
        int spikeCount = window->totalSpikeCount();

        if (i % (pollingWindowSize * numPollingWindows) == 0) {
            stimVector = generateRandomStim(numPollingWindows, num_stims);
        }
        if((i % pollingWindowSize) == 0 && !previousBurstInDesiredDirection){
            // does this actually need to be casted? assumption: no
            stimulate = stimVector[((i % (pollingWindowSize * numPollingWindows)) / pollingWindowSize)];
        }
        else{
            stimulate = false;
        }
        

        if (blanking > 0) {
            blanking--;
            if (blanking != 0) {
                continue;
            }
        }

        

        if (i % (int)(FRAMES_PER_SEC * 0.01) == 0){
            monitoringLoc = window->getAvgX();
            alldata_file << i + SYS_START_BUFFER + WINDOW << ", " << spikeCount << ", " << monitoringLoc << endl;
        }
   
        if ((i == burstStart + (FRAMES_PER_SEC * 0.01 * locCounter)) && locCounter < capacity){
            locs[locCounter] = window->getAvgX();
            burstSpikeCounts[locCounter] = spikeCount;
            locCounter++;
        }


        if (waveVal == Wave::burstStart) {
            locs[0] = window->getAvgX(); // starting location
            burstSpikeCounts[0] = spikeCount;
            locCounter = 1;
        } else if (waveVal == Wave::leftToRight || waveVal == Wave::rightToLeft) {

            int left_to_right = waveVal == Wave::leftToRight;
            string loc_string = left_to_right ? "left to right" : "right to left";
            cout << loc_string << endl;
            file << "BURST" << endl;

            WaveMetadata metadata = sensor.getMetadata();

            // leftToRight, rightToLeft
            for(int m = 0; m < capacity; m++) {
                file << metadata.burstStartFrame + SYS_START_BUFFER + WINDOW + m * (int)(FRAMES_PER_SEC * 0.01) << ", ";
            }
            file << metadata.maxSpikesFrame + SYS_START_BUFFER + WINDOW;

            file << endl;
            
            for(int m = 0; m < capacity; m++) {
                file << locs[m] << ", ";
            }
            file << metadata.maxSpikesLoc << ", ";

            file << loc_string << endl;
            for(int m = 0; m < capacity; m++) {
                file << burstSpikeCounts[m] << ", ";
            }
            file << metadata.maxSpikes;
            
            file << endl;       

            previousBurstInDesiredDirection = left_to_right;
        }

        //STIMULATE IF APPROPRIATE
        if (stimulate && !bursting){
            maxlab::verifyStatus(maxlab::sendSequence("pulse"));
            cout << i << ": PULSE SENT" << endl;
            // blanking += int(FRAMES_PER_SEC) / 2 + pollingWindowSize;
            blanking += int(FRAMES_PER_SEC)/10 +  pollingWindowSize;
        }
    } 

    cout << "program over  " << endl;
    maxlab::verifyStatus(maxlab::DataStreamerFiltered_close());
    file.close();
    alldata_file.close();
}

vector<int> generateRandomStim(int length, int numStims){
    //length >> numStims.
    vector<int> zerosVector(length, 0);
    vector<int> stimIndices;

    while (stimIndices.size() != numStims){
        int randInt = rand()%length;
        if(find(stimIndices.begin(), stimIndices.end(), randInt) == stimIndices.end()) {
            /* v does not contain x */
            stimIndices.push_back(randInt);
        }
    }

    for (int i = 0; i < stimIndices.size(); i++){
        zerosVector[stimIndices[i]] = 1;
    }
    
    return zerosVector;
}


float framesToSeconds(int frames) {
    float seconds = (float) frames / (float) FRAMES_PER_SEC;
    return seconds;
}

int getMaxElement(vector<int> v){
    int maxVal = INT_MIN;
    for(int i = 0; i < v.size(); i++){
        maxVal = max(v[i], maxVal);
    }
    return maxVal;
}