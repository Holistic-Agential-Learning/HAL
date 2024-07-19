/*
    Run:
            ./mouse_1d [world map] [initial position] [on_maxlab] [config_path] [maxtwo_flag] [well]

    world map: string for 1d world
    initial position: integer
    on_maxlab: flag indicating if it's being run on one of the maxlab machines (1)
                or on a PC (0)
    config_path: string for the path to the configuration file
    maxtwo_flag: flag indicating if it's being run on the maxtwo (1)
    well: int for the index of the well that the experiment is being run on
*/
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
#include "hal.h"
#include <map>

// #include "worldstate.h"

using namespace std;
using namespace maxlab;
//changed



#define SYS_START_BUFFER 5 * FRAMES_PER_SEC
#define TOTAL_ELECTRODES emap.size()
#define MIN_FRAMES 0.1 * FRAMES_PER_SEC
#define WINDOW 0.01 * FRAMES_PER_SEC
#define CHIP_WIDTH 220  //87
#define CHIP_HEIGHT 120


#define USAGE "Usage: ./mouse_1d --config <config_path> \t--durations <durations_path>\n\n\
Options:\n\
\t[--maxtwo]                Indicates running on the MaxTwo\n\
\t[--threshold <value>]     Threshold for burst detection (must be a decimal between 0 and 1)\n\
\t[--minutes <value>]       Number of minutes to run\n\
\t[--well <value>]          Well number\n\
\t[--world <value>]         String representing the layout of the 1D circular world\n\
\t[--loc <value>]           Number indicating the index of the world to start at\n\
\t[--local]                 Indicates running locally\n\
"

#define THRESHOLD_DEFAULT 0.1
#define MINUTES_DEFAULT 15

int FRAMES_PER_SEC = 20000;


struct args {
    bool maxtwo;
    string config_path;
    float threshold;
    int minutes;
    int well;
    string world;
    int loc;
    bool local;
    string durations_path;
    string path;
};



float get_avg_side(ChannelWindow window);
float framesToSeconds(int frames);
int get_max_element(vector<int> v);
void runTrainWaveDirection(string path, ElectrodeMap emap, map<string, int> stimulusDurations, int frames, float threshold, int well, WorldState * world);
map<string, int> readDictCsv(const char *filepath);
void printUsage();
struct args getArgs(int argc, char *argv[]);


void printUsage() {
    cout << USAGE << endl;
}


struct args getArgs(int argc, char *argv[]) {
    struct args ret;
    if ((!checkOption("--durations", argc, argv) || !checkOption("--config", argc, argv) || !checkOption("--folder", argc, argv)) && !checkOption("--local", argc, argv)) {
        printUsage();
        exit(2);
    }
    ret.config_path = getStringArg("--config", argc, argv);
    ret.durations_path = getStringArg("--durations", argc, argv);
    ret.maxtwo = checkOption("--maxtwo", argc, argv);
    ret.local = checkOption("--local", argc, argv);
    ret.path = getStringArg("--folder", argc, argv);

    if (checkOption("--threshold", argc, argv)) {
        ret.threshold = getFloatArg("--threshold", argc, argv);
    } else {
        ret.threshold = THRESHOLD_DEFAULT;
    }

    if (checkOption("--well", argc, argv)) {
        ret.well = getIntArg("--well", argc, argv);
    } else {
        ret.well = 0;
    }

    if (checkOption("--minutes", argc, argv)) {
        ret.minutes = getIntArg("--minutes", argc, argv);
    } else {
        ret.minutes = MINUTES_DEFAULT;
    }

    if (checkOption("--world", argc, argv)) {
        ret.world = getStringArg("--world", argc, argv);
    } else {
        ret.world = "00100";
    }

    if (checkOption("--loc", argc, argv)) {
        ret.loc = getIntArg("--loc", argc, argv);
    } else {
        ret.loc = 0;
    }

    return ret; 
}

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


void runTrainWaveDirection(string path, ElectrodeMap emap, map<string, int> stimulusDurations, int frames, float threshold, int well, WorldState * world) {
     // Open data stream and check that no errors occurred
    maxlab::verifyStatus(maxlab::DataStreamerFiltered_open(maxlab::FilterType::IIR));

    std::fstream file;
    std::fstream alldata_file;
    std::fstream mapdata_file;
    file.open(path + "/burst_direction_" + to_string(well) + ".csv", std::fstream::out);
    alldata_file.open(path + "/alldata_" + to_string(well) + ".csv", std::fstream::out);
    mapdata_file.open(path + "/mapdata_" + to_string(well) + ".csv", std::fstream::out);

    mapdata_file << "frame, worldmap, location" << endl;

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
    // cout << threshold * TOTAL_ELECTRODES << endl;

    bool training = false;

    // the number of frames where the spike count goes over the threshold
    int spikeFrameCount = 0;

    ChannelWindow window = ChannelWindow(WINDOW, emap);
    

    // frame number representing the start of a burst
    int burstStart = 0;

    // frame number representing the end of a burst 
    int burstEnd = 0;

    /* the number of frames since the last frame where the spike count went over
       the threshold */ 
    int noSpikeFrameCount = 0;

    // amount of blanking time
    int blanking = 0;

    

    // number of locs that can be stored
    int capacity = 10; //1 second

    // stores calculated average side at certain frames
    vector<float> locs(capacity);

    // spike count for each calculated location, mirroring locs
    vector <int> burstSpikeCounts(capacity);

    bool firstBurstDone = false;
    int maxSpikesFrame = 0;
    int maxSpikes = 0;
    float maxSpikesLoc = 0;

    // number of locs that are currently being stored
    int locCounter = 0;
    
    float monitoringLoc = 0;

    // stores data for each frame in a 200-frame window
    vector<FilteredFrameData> frameWindow;
    cout << "Processing " << framesToSeconds(frames) / 60.0 << " minutes of neuron activity with a spike threshold of " << threshold << endl;


    // initialize the vector with 200 frames
    for (int i = 0; i < window.length(); i++) {
        maxlab::FilteredFrameData frameData;
        maxlab::Status status = maxlab::DataStreamerFiltered_receiveNextFrame(&frameData);

        if (status == maxlab::Status::MAXLAB_NO_FRAME) {
            i--;
            continue;
        }

        window.add(frameData);
    }

    cout << "Window initialized" << endl;
    // start processing frames
    int stimulus_cooldown = 0;

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
        window.shift(frameData);
        int spikeCount = window.totalSpikeCount();

        
        if (i == 0){
            maxlab::verifyStatus(maxlab::sendSequence("before-training"));
            cout << i << ": before training" << endl;
            training = false;
            //initialize the initial location of the agent.
            maxlab::verifyStatus(maxlab::sendSequence(("move_to_" + to_string(world->location)).c_str()));
            mapdata_file << 0 << ", " << world->world_map << ", " << world->location  << endl;

        }
        else if (i == (int)((float)(frames)/2)) {
            maxlab::verifyStatus(maxlab::sendSequence("training"));
            cout << i << ": training" << endl;
            training = true;
        }
        // else if (i == (int)((float)(2*frames)/3)) {
        //     maxlab::verifyStatus(maxlab::sendSequence("after-training"));
        //     cout << i << ": after training" << endl;
        //     training = false;
        // }

        if (stimulus_cooldown > 0){
            if(stimulus_cooldown == 1){
                cout << "stimulus_cooldown done" << endl;
            }
            stimulus_cooldown--;
        }

        if (blanking > 0){
            if (blanking == 1){
                cout << "blanking done" << endl;
            }
            blanking--;
            continue;
            cout << "hi" << endl;
        }
        
        //check the world state, determine stimuli appropriately.
        if (stimulus_cooldown <= 0 && training){
            string stimulus_name = "loc" + to_string(world->location) + "_distance";
            int duration = stimulusDurations[stimulus_name];
            
            maxlab::verifyStatus(maxlab::sendSequence(stimulus_name.c_str()));

            stimulus_cooldown += (duration + FRAMES_PER_SEC/100);
        }


        if (i % (int)(FRAMES_PER_SEC * 0.01) == 0){
            //monitoringLoc = get_avg_side(window);
            monitoringLoc = window.getAvgX();
            alldata_file << i + SYS_START_BUFFER + WINDOW << ", " << spikeCount << ", " << monitoringLoc << endl;
        }
   
        if ((i == burstStart + (FRAMES_PER_SEC * 0.01 * locCounter)) && locCounter < capacity){
            locs[locCounter] = window.getAvgX();
            burstSpikeCounts[locCounter] = spikeCount;
            locCounter++;
        }
        
        // if the current spike count is over the threshold
        if  (spikeCount > threshold * TOTAL_ELECTRODES) {

            if (!firstBurstDone && spikeCount > maxSpikes && i % (int)(FRAMES_PER_SEC * 0.005) == 0){
                maxSpikes = spikeCount;
                maxSpikesFrame = i;
                maxSpikesLoc = window.getAvgX();
            }

            // start of the burst
            if (noSpikeFrameCount > 0 && spikeFrameCount == 0) { 
                locs[0] = window.getAvgX(); // starting location
                burstSpikeCounts[0] = spikeCount;
                locCounter = 1;
                burstStart = i;
            }
            
            spikeFrameCount++; // spike at this frame
            noSpikeFrameCount = 0;
        } else {
            //First burst is done.
            if (!firstBurstDone && noSpikeFrameCount > 0.2 * FRAMES_PER_SEC) {
                firstBurstDone = true;
                
            }
            // burst is over
            if (noSpikeFrameCount > 1 * FRAMES_PER_SEC) {
                // burst is long enough to be significant
                if (spikeFrameCount >= MIN_FRAMES) {
                    
                    // // edge case: startingLocDiff = 0 (right for now)
                    int left_to_right = locs[0] < maxSpikesLoc;
                    string loc_string = left_to_right ? "left to right" : "right to left";
                    file <<"BURST" << endl;
                    for(int m = 0; m < capacity; m++) {
                        file << burstStart + SYS_START_BUFFER + WINDOW + m * (int)(FRAMES_PER_SEC * 0.01) << ", ";
                    }
                    file << maxSpikesFrame + SYS_START_BUFFER + WINDOW;

                    file << endl;
                    
                    for(int m = 0; m < capacity; m++) {
                        file << locs[m] << ", ";
                    }
                    file << maxSpikesLoc << ", ";

                    file << loc_string << endl;
                    for(int m = 0; m < capacity; m++) {
                        file << burstSpikeCounts[m] << ", ";
                    }
                    file << maxSpikes;
                    
                    file << endl;

 
                    if (left_to_right) {
                        world->move_right();
                    } 
                    else {
                        world->move_left();
                    }
                    string position = string{world->get_position()};
                    cout << "moved to position " << position << endl;
                    cout << "sending sequence " << ("move_to_" + to_string(world->location)).c_str() << endl;
                    maxlab::verifyStatus(maxlab::sendSequence(("move_to_" + to_string(world->location)).c_str()));
                    mapdata_file << i + SYS_START_BUFFER + WINDOW << ", " << world->world_map << ", " << world->location  << endl;

                    if (stimulusDurations.count(position) > 0 && training){
                        //we are at a point of interest
                        cout << "AT POINT OF INTEREST" << endl;
                        int duration = stimulusDurations[position];
                        cout << "duration: " << duration << endl;
                        
                        maxlab::verifyStatus(maxlab::sendSequence(position.c_str()));
                        
                        stimulus_cooldown += (duration + FRAMES_PER_SEC/100);
                        blanking += (duration + FRAMES_PER_SEC/100);

                    }
                }    
                firstBurstDone = false;
                maxSpikes = 0;  
                spikeFrameCount = 0;
            }
            noSpikeFrameCount++;
        }
    } 

    cout << "program over  " << endl;
    maxlab::verifyStatus(maxlab::DataStreamerFiltered_close());
    file.close();
    alldata_file.close();
    mapdata_file.close();
}


/* get_avg_side
 * 
 * Returns the average starting column of the spike events in a given window
 * 
 * Parameters:
 *      frameWindow: vector of FilteredFrameData structs, representing a 
 *                   200-frame window of frame data
 *  
 */
float get_avg_side(ChannelWindow window) {
    ElectrodeMap emap = window.electrodeMap();

    // used to make sure that each channel is only counted once
    int channels[1024];
    float sum = 0;
    float count = 0;
    for (int i = 0; i < window.length(); i++) {
        FilteredFrameData fd = window.get(i);
        const SpikeEvent *event = fd.spikeEvents;
        int spikeCount = fd.spikeCount;
        for (int j = 0; j < spikeCount; j++) {
            // compute column coordinate and add to sum
            int channel = event[j].channel;
            // if the channel has already been counted
            if (channel < 1024 && channels[channel] == 0) {
                if(channel > 1024) {
                    cout << "ERROR WITH CHANNEL NUMBER- TOO HIGH" << endl;
                }
                float x_coord = emap.get_x(channel);
                if(x_coord < 0){ //channel number not found in the emap
                    // cout << "channel number " << channel << " fired, but is not in the channel mapping" << endl;
                }
                else {
                    sum += x_coord;
                    channels[channel] = 1;
                    count++;
                }
            }
            
        }
    }
    return sum / count;
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

//THIS COULD PROBABLY GO INTO SOME UTILS PACKAGE
/* readDictCsv
 * 
 * Reads a CSV made with a dictionary from python with keys in one column and values in another.
 * For the future, needs to be made type-general.
 * 
 */
map<string, int> readDictCsv(const char *filepath){
    std::ifstream fin(filepath);
    if (!fin) { 
        cout << "Error, could not open file." << endl; 
        exit(2);
    }

    map<string, int> dict;

    string key;
    string value;

    // while (fin >> key >> value){
    //     dict[key] = value;
    // }
    while(getline(fin, key, ',')){
        getline(fin, value);

        dict[key] = stoi(value);
    }

    fin.close();

    return dict;

}

int main(int argc, char * argv[]) {
    //NECESSARY PARAMS
    // default process 1200000 frames (1 minute)
    // sleep(600+15);
    struct args params = getArgs(argc, argv);
    WorldState world = WorldState(params.world, params.loc);
    
    int maxlab = !params.local;

    world.display();
    
    if(!maxlab){
        bool next = true;
        cout << "Press x to escape. Use arrow keys to go right/left, followed by enter. "<< endl;
        while(next){
            int a = cin.get();
            switch(a){
                case 67://right
                    world.move_right();
                    cout << "at position " << world.get_position() << endl;
                break;
                case 68: //left
                    world.move_left();
                    cout << "at position " << world.get_position() << endl;
                break;
                case 'x': //esc
                    next = false;
                break;
            }
        }
        
    }
    else{
        const char *configPath = params.config_path.c_str();
        const char *durationsPath = params.durations_path.c_str();
        ElectrodeMap emap = ElectrodeMap(configPath);


        //READ IN DURATIONSPATH CSV
        map<string, int> stimulusDurations = readDictCsv(durationsPath);

        int well = params.well;
        
        if(params.maxtwo) {
            FRAMES_PER_SEC = 10000;
        }
        
        int frames = params.minutes*60*FRAMES_PER_SEC;
        
        float threshold = params.threshold;

        string path = params.path;

        cout << "Frames per sec: " << FRAMES_PER_SEC << endl;
        cout << "Min frames: " << MIN_FRAMES << endl;

        try{
            runTrainWaveDirection(path, emap, stimulusDurations, frames, threshold, well, &world);
        } catch (int err) {
            cout << "Program failed with error code " << err << endl;
            maxlab::verifyStatus(maxlab::DataStreamerFiltered_close());
            return err;
        }
        
        //copied from stim-burst-side.cpp
    }
 
    return 0;
}
