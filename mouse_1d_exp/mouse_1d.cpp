#include <stdlib.h>
#include <stdio.h>
#include <iostream>
#include <unistd.h>
#include <maxlab.h>
#include <signal.h>
//#include <cassert>
#include <vector>

#include "worldstate.h"

using namespace std;
using namespace maxlab;
//changed




//THIS FIRST CHUNK OF CODE IS JUST COPIED FROM STIM-BURST-SIDE. NEEDS TO BE CLEANED UP...
#define SYS_START_BUFFER 100000
#define TOTAL_ELECTRODES 1019
#define MIN_FRAMES 2000
#define WINDOW 200
#define FRAMES_PER_SEC 20000
#define CHIP_WIDTH 220  //87
#define CHIP_HEIGHT 120


void signal_interrupt_handler(int sig) {
    cout << "^C signalled!" << endl;
    maxlab::verifyStatus(maxlab::DataStreamerFiltered_close());
    exit(sig);
}





void print_starting_location(vector<const SpikeEvent *> spikeEvents, vector<int> spikeCounts) {
    int sum = 0;
    int count = 0;
    for (int i = 0; i < spikeEvents.size() / 4; i++) {
        // cout << "getting frame " << i << endl;
        const SpikeEvent *event = spikeEvents[i];
        for (int j = 0; j < spikeCounts[i]; j++) {
            // cout << "getting channel " << event[j].channel << endl;
            sum += event[j].channel % CHIP_WIDTH;
            count++;
        }
    }
    cout << count << " spikes on first quarter of window" << endl;
    cout << "First half of spike window starting side: " << (float) sum / (float) count << endl;
    sum = 0;
    count = 0;
    for (int i = spikeEvents.size() / 4 * 3; i < spikeEvents.size(); i++) {
        const SpikeEvent *event = spikeEvents[i];
        for (int j = 0; j < spikeCounts[i]; j++) {
            sum += event[j].channel % CHIP_WIDTH;
            count++;
        }
    }

    cout << count << " spikes on fourth quarter of window" << endl;
    cout << "Second half of spike window starting side: " << (float) sum / (float) count << endl;

}

/* get_avg_side
 * 
 * Returns the average starting column of the spike events in a given window
 * 
 * Parameters:
 *      spikeEvents: window (vector) of SpikeEvent structs
 *      spikeCounts: vector (mirroring spikeEvents) of the number of spikes in 
 *                   the corresponding spikeEvent
 *  
 */
float get_avg_side(vector<const SpikeEvent *> spikeEvents, vector<int> spikeCounts) {
    float sum = 0;
    float count = 0;
    for (int i = 0; i < spikeEvents.size(); i++) {
        const SpikeEvent *event = spikeEvents[i];
        for (int j = 0; j < spikeCounts[i]; j++) {
            // compute column coordinate and add to sum
            sum += event[j].channel % CHIP_WIDTH; 
            count++;
        }
    }

    return sum / count;
}

/* get_side_diff
 * 
 * Returns the difference of the number of spikes on the left side of the chip 
 * and the right side of the chip. A positive integer indicates more spikes on 
 * the left side, and a positive integer indicates more spikes on the right.
 * 
 * Parameters:
 *      spikeEvents: window (vector) of SpikeEvent structs
 *      spikeCounts: vector (mirroring spikeEvents) of the number of spikes 
 *                   in the corresponding spikeEvent
 *  
 */
int get_side_diff(vector<const SpikeEvent *> spikeEvents, vector<int> spikeCounts) {
    int middle = CHIP_WIDTH / 2;
    int result = 0;
    for (int i = 0; i < spikeEvents.size(); i++) {

        const SpikeEvent *event = spikeEvents[i];

        for (int j = 0; j < spikeCounts[i]; j++) {
            int location = event[j].channel % CHIP_WIDTH; 

            // add one if on the left, subtract one if on the right
            result += (location < middle) ? -1 : 1;
        }
    }

    return result;
}

float framesToSeconds(int frames) {
    float seconds = (float) frames / (float) FRAMES_PER_SEC;
    return seconds;
}





void run_stim_burst_side(WorldState * world){
    // default process 1200000 frames (1 minute)
    // sleep(600+15);
    int frames = 15*60*20000;
    float threshold = 0.1;
    
    // if (argc >= 2) {
    //     frames = stoi(argv[1]);
    // } if (argc >= 3) {
    //     threshold = stof(argv[2]);
    // }

    cout << "Processing " << framesToSeconds(frames) / 60 << " minutes of neuron activity with a spike threshold of " << threshold << endl;

    // activate interrupt handler
    signal(SIGINT, signal_interrupt_handler);

    // Keep in mind that start up causes a lot of spikes

    // Open data stream and check that no errors occurred
    maxlab::verifyStatus(maxlab::DataStreamerFiltered_open(maxlab::FilterType::IIR));
    
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

    int spikeWindowCount = 0;
    int spikeFrameCount = 0;
    int noSpikeFrameCount = 0;
    int spikeCount = 0;
    int lastSpike = 0;
    int blanking = 0;
    float startingLoc = 0;
    int startingLocDiff = 0;
    vector<int> spikeCountWindow;
    vector<const SpikeEvent *> spikeEventWindow;
    cout << "Initial vector size: " << spikeCountWindow.size() << endl;

    // initialize the vector with 200 frames
    for (int i = 0; i < WINDOW; i++) {
        maxlab::FilteredFrameData frameData;
        maxlab::Status status = maxlab::DataStreamerFiltered_receiveNextFrame(&frameData);

        if (status == maxlab::Status::MAXLAB_NO_FRAME) {
            i--;
            continue;
        }
        spikeCount += frameData.spikeCount;

        spikeCountWindow.push_back(frameData.spikeCount);
        spikeEventWindow.push_back(frameData.spikeEvents);
    }


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

        int oldSpikeCount = spikeCountWindow[0];

        spikeCountWindow.erase(spikeCountWindow.begin());
        spikeEventWindow.erase(spikeEventWindow.begin());
        
        spikeCount -= oldSpikeCount; 
        spikeCount += frameData.spikeCount;

        spikeCountWindow.push_back(frameData.spikeCount);
        spikeEventWindow.push_back(frameData.spikeEvents);

        if (blanking > 0) {
            blanking--;
            if (blanking != 0) {
                continue;
            }
        }
   
        
        if  (spikeCount > threshold * TOTAL_ELECTRODES) {
            if (noSpikeFrameCount > 0 && spikeFrameCount == 0) {
                // cout << "_____________________________" << endl;
                // cout << i << ": Buffer lasting " << noSpikeFrameCount << " frames" << endl;
                // print_starting_location(spikeEventWindow, spikeCountWindow);
                startingLoc = get_avg_side(spikeEventWindow, spikeCountWindow);
                startingLocDiff = get_side_diff(spikeEventWindow, spikeCountWindow);
            }
            spikeFrameCount++; // spike at this frame
            noSpikeFrameCount = 0;
        } else {
            // cout << (spikeWindowCount) << " vs " << (threshold * TOTAL_ELECTRODES) << endl;
             
            if (noSpikeFrameCount > 200) {
                if (spikeFrameCount >= MIN_FRAMES) {
                    cout << "^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^" << endl;
                    float seconds = framesToSeconds(spikeFrameCount);
                    cout << "Detected burst lasting " << seconds << " seconds (" << spikeFrameCount << " frames), starting at position " << startingLoc << endl;

                    // edge case: startingLocDiff = 0 (right for now)
                    int left = startingLocDiff < 0;
                    string loc = left ? "left" : "right";
                    int numSide = startingLocDiff * (left ? -1 : 1);

                    cout << numSide << " extra spikes on the " << loc << " side" << endl;
                    // print_starting_location(spikeEventWindow, spikeCountWindow);

                    //NOTE: THIS SECTION HERE IS CHANGED FROM THE ORIGINAL!!!
                    if (left) {
                        //maxlab::verifyStatus(maxlab::sendSequence("stim_seq"));
                        //cout << i << ": sent stimulation after burst of " << seconds << " seconds (" << spikeFrameCount << " frames)" << endl;
                        //blanking = 8000;
                        world->move_left();
                    }
                    else{
                        world->move_right();
                    }
                    cout << "frame no: " << i << endl;
                    //End change
                }      
                spikeFrameCount = 0;
            }
            noSpikeFrameCount++;
        }
    } 

    cout << "program over  " << endl;
    maxlab::verifyStatus(maxlab::DataStreamerFiltered_close());
}





















bool run_experiment(WorldState * world, bool maxlab){
    if(!maxlab){
        bool next = true;
        cout << "Press x to escape. Use arrow keys to go right/left, followed by enter. "<< endl;
        while(next){
            int a = cin.get();
            switch(a){
                case 67://right
                    world->move_right();
                break;
                case 68: //left
                    world->move_left();
                break;
                case 'x': //esc
                    next = false;
                break;
            }
        }
        
    }
    else{
        run_stim_burst_side(world);
        //copied from stim-burst-side.cpp
    }

    return true;
}



int main(int argc, char * argv[]) {
    //Params to the c++ file:
    //  world: a string representing the 1D world.
    // Location: a 0-indexed int that represents the starting position of the mouse.
    // maxlab: Whether or not to run the maxlab program. If it's 0, run it locally. Defaults to 1 (run on maxlab machine).
    WorldState world;
    if(argc >= 3){
        world = WorldState(argv[1], stoi(argv[2]));
    }
    else{
        world = WorldState();
    } 

    int maxlab = 1;

    if (argc >= 4){
        maxlab = stoi(argv[3]);
    }
    world.display();
    
    run_experiment(&world, maxlab != 0); //with some regularity, reset locations.

    cout << "print statistics" << endl;

    return 0;
}