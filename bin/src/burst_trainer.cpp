// This is a new experiment written by Wesley Clawson trying to reproduce
// the original 'wave training'. 
// Trevor implementation: train-wave.cpp
// original Nathan: rp_stim_removal.cpp

// Includes for a variety of stuff - nothing custom
#include <stdlib.h>
#include <stdio.h>
#include <iostream>
#include <unistd.h>
#include <algorithm>
#include <signal.h>
#include <vector>
#include <fstream>
#include <assert.h>
#include <limits.h>
#include <random>
#include <string>
#include <map>
#include <time.h>
#include <iomanip>  // for std::setw

// this needs to be included to use of HALs custom classes, such as 
// channelWindow, WaveDetector, and StimVector
#include "hal.h"

// Colors b/c I like pretty things
// ANSI color codes
const string CYAN = "\033[36m";
const string YELLOW = "\033[33m";
const string GREEN = "\033[32m";
const string RESET = "\033[0m";
const string BOLD = "\033[1m";

// Namespaces to make things easier
using namespace std;        //common namespace for things like cout
using namespace argparse;   //used so that we can take arguments from python
using namespace maxlab;     //the maxlab namespace

// Usage statement in case someone ever wants to run it from CLI
const char* USAGE = R"(Usage: ./new-train-wave --config <file> --folder <path> [--maxtwo] [--pulse-duration <value>] [--threshold <value>] [--minutes <value>] [--well <value>]

Options:
    --config <file>                 Full path to configuration file for experiment
    --folder <path>                 Full path to parent folder for saving data
    --maxtwo                        Indicates running on the MaxTwo
    --pulse-duration <value>        Duration of a single pulse, in second, default 0.0002
    --stim-rate <value>             Stimulation rate, in stimulations per second, default 5
    --threshold <value>             Threshold for burst detection, float between 0 and 1, default (window length) / 1000
    --minutes <value>               Number of minutes to run the experiment, default 15
    --well <value>                  Well number, default 0
)";

////////////////////////////////////////////////////
////////// PARAMETER TIME, BABY ////////////////////
////////////////////////////////////////////////////

// Some global parameters that are pretty standard
#define RANDOM_SEED 10                      /* fixed random seed */
#define CHIP_WIDTH 220      /* This is how many electrodes in X (L/R will use CHIP_WIDTH / 2) */
#define CHIP_HEIGHT 120     /* This is how many electrodes in Y */

//////////////////////////////////////////////////////////////////////////
// DEFAULTS - WILL MOST LIKELY BE REPLACED BY INPUT FROM USER 
// VIA THE PYTHON FILE. This is the way. 
//////////////////////////////////////////////////////////////////////////

// Experimental setup defaults
#define DEFAULT_WELL 0       /* Default well*/
#define DEFAULT_RIGHTBURST 2 /* default behavior state for a right burst */
#define DEFAULT_LEFTBURST 0  /* default behavior state for a left burst */

// Timing defaults
#define PRE_MINUTES_DEFAULT 20      /* 20 min */
#define TRAIN_MINUTES_DEFAULT 20    /* 20 min */
#define POST_MINUTES_DEFAULT 20     /* 20 min */

// Stimulation defaults
#define STIM_PULSE_DUR_DEFAULT 0.0002   /* How long the square pulse is in s (total dur is 2X this) */
#define STIM_RATE_DEFAULT 5             /* 5 Hz (stims per second) */
#define RANDOM_WINDOW_GEN_TIME 5        /* generate randomness over 5 second intervals */

////////////////////////////////////////////////////
////////// PROTOTYPES AND ^C ///////////////////////
////////////////////////////////////////////////////

//  Some quick function setup (called prototypes)
//  They provide the compiler with information about the signature of the functions;
//  what types of arguments they take, and what type they return.

// Converts frames to seconds b/c it's easier sometimes
float framesToSeconds(int frames, int framesPerSec);
int secondsToFrames(float seconds, int framesPerSec);

// This function actually holds the experimental logic (aka the meat)
void runExperiment(string path, string configPath, int well, int framesPerSec, 
    int pre_frames, int train_frames, int post_frames,
    float burst_size_threshold, float burst_dur_threshold,
    float stimRate, float pulseDurationSecs,
    int leftburst, int rightburst);

/**
 * @brief Handles Ctrl+C interrupt signal (SIGINT).
 * 
 * Close everything w/o breaking it if you Ctrl+C to cancel experiment.
 * Data WILL still save, so that's nice. 
 *
 * @param sig The signal number (typically SIGINT).
 */
void signal_interrupt_handler(int sig) {
    cout << " signalled!" << endl;
    maxlab::verifyStatus(maxlab::DataStreamerFiltered_close());
    exit(sig);
}

// A logger for bursts - every burst should now log in a small file. yay.
void saveBurstData(const WaveMetadata& metadata,
    std::ostream& file,
    float* locs,
    int* burstSpikeCounts,
    int capacity,
    int framesPerSec,
    int SYS_START_BUFFER,
    int WINDOW,
    const std::string& directionString)
{
    static bool wroteHeader = false;

    if (!wroteHeader) {
    // --- Header: Frame times ---
    for (int m = 0; m < capacity; m++) {
    file << "T+" << m * 10 << "ms,";
    }
    file << "PeakFrame,";

    // --- Header: Locations ---
    for (int m = 0; m < capacity; m++) {
    file << "Loc" << m << ",";
    }
    file << "PeakLoc,BurstStartDet,Direction,";

    // --- Header: Spike Counts ---
    for (int m = 0; m < capacity; m++) {
    file << "Spikes" << m << ",";
    }

    // --- Header: Burst Duration ---
    file << "PeakSpikes,FramesAboveThreshold\n";

    wroteHeader = true;
    }

    // --- Row: Frame times ---
    for (int m = 0; m < capacity; m++) {
    int frameTime = metadata.burstStartFrame + SYS_START_BUFFER + WINDOW + m * static_cast<int>(framesPerSec * 0.01);
    file << frameTime << ",";
    }
    file << (metadata.maxSpikesFrame + SYS_START_BUFFER + WINDOW) << ",";

    // --- Row: Locations ---
    for (int m = 0; m < capacity; m++) {
    file << locs[m] << ",";
    }
    file << metadata.maxSpikesLoc << "," << metadata.burstStartLocation << "," << directionString << ",";

    // --- Row: Spike Counts ---
    for (int m = 0; m < capacity; m++) {
    file << burstSpikeCounts[m] << ",";
    }

    // --- Row: Peak Spikes & How long Burst lasts ---
    file << metadata.maxSpikes << "," << metadata.framesAboveThreshold << "\n";
}


/** HELPER FUNCTIONS BELOW
 *  
 *  1. framesToSeconds - Convert frames to seconds
 *  2. secondsToFrames - Convert seconds to frames
 */
float framesToSeconds(int frames, int framesPerSec) {
    return static_cast<float>(frames) / framesPerSec;
}

int secondsToFrames(float seconds, int framesPerSec) {
    return static_cast<int>(seconds * framesPerSec);
}

////////////////////////////////////////////////////
////////// ONTO THE GOOD STUFF /////////////////////
////////////////////////////////////////////////////

/** 
 * This is the 'main' code of c++ - it will call 'runExperiment' at the end.
 * It's main purpose is to pull in paramters from python file and setup the basics. 
*/
int main(int argc, char * argv[]) {
    // --------------------------------------------
    // --- Parse arguments from the python file ---
    // --------------------------------------------

    // Get the data path needed for saving and locate the needed configs for the recordings
    string folderPath = getStringArg("--folder", argc, argv, USAGE);     // This sets where saving happens 
    string configPath = getStringArg("--config", argc, argv, USAGE);     // Where is your config
    
    // Do you have a M1 or M2, and which well are you doing this on?
    bool maxtwo = checkOption("--maxtwo", argc, argv);  // Are you using a MaxTwo or not
    int well = getIntArgSecure("--well", DEFAULT_WELL, argc, argv);    // Which well are you going to work on
    
    // --- Set sampling rate based on device type ---
    int framesPerSec = maxtwo ? 10000 : 20000;

    // --- This will set flags for the stimulation behavior --- 
    // --- default: right == random, left == nothing
    int rightburst = getIntArgSecure("--right-type", DEFAULT_RIGHTBURST, argc, argv);   // stimulation for rightburst, default Random
    int leftburst = getIntArgSecure("--left-type", DEFAULT_LEFTBURST, argc, argv);    // stimulation for leftburst, default Nothing

    // --- This will set flags for the burst detection behavior --- 
    const float BURST_DURATION_THRESHOLD_DEFAULT = static_cast<int>(0.1 * framesPerSec);  // default behavior
    const float BURST_SIZE_THRESHOLD_DEFAULT = 0.15f;                                    /* activity burst threshold */

    float burst_size_threshold = getFloatArgSecure("--burst_size_threshold", BURST_SIZE_THRESHOLD_DEFAULT, argc, argv);  // How big (% of channels) a burst needs to be to count it
    float burst_dur_threshold = getFloatArgSecure("--burst_dur_threshold", BURST_DURATION_THRESHOLD_DEFAULT, argc, argv);  // How many seconds of a burst needed before we count it as a burst
    
    // Stimulation parameters
    float stimRate = getFloatArgSecure("--stim-rate", STIM_RATE_DEFAULT, argc, argv);   // Stim rate in Hz
    float pulseDurationSecs = getFloatArgSecure("--pulse-duration", STIM_PULSE_DUR_DEFAULT, argc, argv);    // How long a pulse is in sec (normally 400 us)
    
    // Timing parameters
    float pre_mins = getIntArgSecure("--pre-recording", PRE_MINUTES_DEFAULT, argc, argv);   // How long you want pre training to last
    float train_mins = getFloatArgSecure("--minutes", TRAIN_MINUTES_DEFAULT, argc, argv);   // How long you want training to last
    float post_mins = getIntArgSecure("--post-recording", POST_MINUTES_DEFAULT, argc, argv);// How long you want post training to last
    float total_time = pre_mins + train_mins + post_mins;

    // Same timing parameters, but in frames
    int pre_frames = secondsToFrames(pre_mins*60, framesPerSec);      // # frames to record before training; mins * 60 sec / min * frames per sec
    int train_frames = secondsToFrames(train_mins*60, framesPerSec);  // # frames to record during training; mins * 60 sec / min * frames per sec
    int post_frames = secondsToFrames(post_mins*60, framesPerSec);    // # frames to record after training; mins * 60 sec / min * frames per sec

    // Print pretty things to let the user know all the details of the run
    cout << BOLD << CYAN << "\n===== Experiment Setup =====" << RESET << endl;
    cout << left << setw(15) << (YELLOW + "Device:")     << RESET << "Max" << (maxtwo ? "TWO" : "ONE") << endl;
    cout << left << setw(15) << (YELLOW + "Config:")     << RESET << configPath << endl;
    cout << left << setw(15) << (YELLOW + "Well:")       << RESET << well << endl;
    cout << BOLD << CYAN << "\n===== Burst Detection =====" << RESET << endl;
    cout << left << setw(15) << (YELLOW + "Size Threshold:")  << RESET << burst_size_threshold << endl;
    cout << left << setw(15) << (YELLOW + "Duration Threshold:")  << RESET << burst_dur_threshold << endl;
    cout << BOLD << CYAN << "\n===== Experimental Time =====" << RESET << endl;
    cout << left << setw(15) << (YELLOW + "Pretrain:")   << RESET << pre_mins << " mins" << endl;
    cout << left << setw(15) << (YELLOW + "Training:")   << RESET << train_mins << " mins" << endl;
    cout << left << setw(15) << (YELLOW + "Posttrain:")  << RESET << post_mins << " mins" << endl;
    cout << left << setw(15) << (YELLOW + "Total time:") << RESET << GREEN << total_time << " mins" << RESET << endl;
    cout << BOLD << CYAN << "=============================\n" << RESET << endl;

    ElectrodeMap emap = ElectrodeMap(configPath.c_str());

    try {
        runExperiment(folderPath, configPath, well, framesPerSec, pre_frames, train_frames, post_frames, burst_size_threshold, burst_dur_threshold, stimRate, pulseDurationSecs, leftburst, rightburst);
    } catch (int& err) {
        cout << "Program failed with error code " << err << endl;
        maxlab::verifyStatus(maxlab::DataStreamerFiltered_close());
        return err;
    }

    return 0;
}

/** 
 * This is the 'experimental part' of the code - it runs the real-time analysis/detection of bursts
 * It's main purpose is to detect bursts, figure out where they came from LvR, and deliever the appropriate stimulation. 
*/
void runExperiment(string path, string configPath, int well, int framesPerSec, int pre_frames, int train_frames, int post_frames, float burst_size_threshold, float burst_dur_threshold, float stimRate, float pulseDurationSecs, int leftburst, int rightburst){  
    // =====================================================
    //                     Setup Phase
    // =====================================================
    
    // These are important. 
    // This will set how long ChannelWindow is in frames
    // (ChannelWindow collects spikesrates over the window)
    const int WINDOW = static_cast<int>(0.02 * framesPerSec);    
    const int SYS_START_BUFFER = 5 * framesPerSec;  // The system takes ~5 seconds to stabilize

    // At this time, capacity and locs are only for logging purpose. Functionally, they do nothing. 
    const int capacity = 10; // 1 second -> 
    int locCounter = 0;
    float locs[capacity] = {0.0};
    int burstSpikeCounts[capacity] = {0};

    /**
     * @brief Struct for holding the internal state of the experiment during training.
     */
    struct ExperimentState {
        bool bursting = false;      // this should get thrown if there's a true burst 
        bool burstStart = false;    // this is if the threshold is crossed, but not a full burst yet
        int blanking = 0;
        int previousBurst = 0;
        int lastBurstStartFrame = 0;
    };
    
    maxlab::verifyStatus(maxlab::DataStreamerFiltered_open(maxlab::FilterType::IIR));

    // This will start the saving the CSV that's used for debugging/analysis after the experiment
    std::fstream alldata_file;
    std::ofstream file(path + "/burst_direction_" + std::to_string(well) + ".csv", std::ios::out);
    alldata_file.open(path + "/alldata_" + to_string(well) + ".csv", std::fstream::out);

    // Activate interrupt handler
    signal(SIGINT, signal_interrupt_handler);

    // Start up causes a lot of spikes and we don't want to accidentally detect this. 
    // We don't record the system startup stuff
    for (int i = 0; i < SYS_START_BUFFER; i++) {
        maxlab::FilteredFrameData frameData;
        maxlab::Status status = maxlab::DataStreamerFiltered_receiveNextFrame(&frameData);
        if (status == maxlab::Status::MAXLAB_NO_FRAME) {
            i--;
            continue;
        }
    }

    // =====================================================
    //                     Experimental Setup
    // =====================================================

    ExperimentState state; // Create the ExperimentalState struct that holds what we need

    // Instantiate stimulation vectors.
    // User selects type: 0 = off, 1 = regular, 2 = random.
    // If stimRate is set to 0, StimVector will disable all stimulation.
    StimVector rightStim = StimVector(
        rightburst == 2,
        rightburst == 0 ? 0 : stimRate, // This checks rightStim is 0, if so pass '0 Hz' to stimVector, else pass stimRate
        framesPerSec,
        0.001
    );

    StimVector leftStim = StimVector(
        leftburst == 2,
        leftburst == 0 ? 0 : stimRate,  // This checks leftStim is 0, if so pass '0 Hz' to stimVector, else pass stimRate
        framesPerSec,
        0.001
    );

    cout << "Left burst in cpp: " << leftburst << endl;
    cout << "Right burst in cpp: " << rightburst << endl;

    // gets wave detector object and initializes window
    WaveDetector sensor = WaveDetector(WINDOW, configPath.c_str(), framesPerSec, burst_size_threshold, burst_dur_threshold, 0.05);
    ChannelWindow *window = sensor.getWindow();
    
    // =====================================================
    //                     Pre-Training Phase
    // =====================================================
    cout << BOLD << CYAN << "\n===== Pretraining =====" << RESET << endl;
    cout << left << setw(15) << (YELLOW + "Recording:") << RESET << framesToSeconds(pre_frames, framesPerSec) / 60.0 << (YELLOW + " minutes of neuron activity") << endl;
    ProgressBar preBar = ProgressBar(pre_frames, "Recording...");

    // this line send an event to the system for tracking in the raw data
    maxlab::verifyStatus(maxlab::sendSequence(("pre_recording_start_" + to_string(well)).c_str())); 

    // The actual loop that goes through pre_frames
    for (int i = 0; i < pre_frames; i++) {
        maxlab::FilteredFrameData frameData;
        maxlab::Status status = maxlab::DataStreamerFiltered_receiveNextFrame(&frameData);
        if (status == maxlab::Status::MAXLAB_NO_FRAME) {
            i--;                // Retry if no frame
            continue;
        }

        // Important in alpha - don't process all frames
        if (frameData.frameInfo.well_id != well) {
            i--;  // don't advance if wrong well
            // cout << "well: " << static_cast<int>(frameData.frameInfo.well_id) << endl;
            continue;
        }

        preBar.increment();
    }

    // Define blanking time
    const int BLANKING_FRAMES = static_cast<int>(4 * pulseDurationSecs * framesPerSec);  // Blank for four times the entire square pulse (duration X 4)

    // =====================================================
    //                     Training Phase
    // =====================================================
    cout << BOLD << CYAN << "\n===== Training! =====" << RESET << endl;
    cout << left << setw(15) << (YELLOW + "Processing:") << RESET << framesToSeconds(train_frames, framesPerSec) / 60.0 << (YELLOW + " minutes of neuron activity") << endl;
    ProgressBar expBar = ProgressBar(train_frames, "Training...");

    // This send an event to the system so that you have an event with the frame number where the training started
    maxlab::verifyStatus(maxlab::sendSequence(("closed_loop_start_" + to_string(well)).c_str()));

    // make a variable that checks if a burst has been dealt with, then waits for another
    bool directionHandled = false;
    cout << train_frames << endl;
    // This is the main loop that goes through training frame by frame (i is frame)
    for (int i = 0; i < train_frames; i++) {
        
        // === 1. Receive Frame ===
        maxlab::FilteredFrameData frameData;
        maxlab::Status status = maxlab::DataStreamerFiltered_receiveNextFrame(&frameData);
        // std::cout << "frame status: " << static_cast<int>(status) << std::endl;

        if (status == maxlab::Status::MAXLAB_NO_FRAME) {
            i--; // Retry if no frame was received
            continue;
        }

        // Important in alpha - don't process all frames
        if (frameData.frameInfo.well_id != well) {
            i--;  // don't advance if wrong well
            continue;
        }

        //expBar.increment(); // Update progress bar

        // === 2. Process Frame ===
        int waveVal = sensor.processFrame(frameData, i);
        int spikeCount = sensor.getWindow()->totalSpikeCount();

        // === 3. Handle Blanking Countdown ===
        if (state.blanking > 0) {
            state.blanking--;
        }

        // === 4. If not blanking, monitor & detect bursts ===
        if (state.blanking == 0) {

            // --- 4A. Periodic Logging ---
            if (i % static_cast<int>(framesPerSec * 0.1) == 0) {
                float monitoringLoc = sensor.getWindow()->getAvgX();
                alldata_file << (i + SYS_START_BUFFER + WINDOW) << ", "
                            << spikeCount << ", "
                            << monitoringLoc << endl;
            }
            
            // --- 4Ba. Detect New Burst Start ---
            // --- This is for tracking locs for evolution ---
            if (waveVal == Wave::burstStart) {
                locs[0] = sensor.getWindow()->getAvgX();
                burstSpikeCounts[0] = spikeCount;
                locCounter = 1;
                state.lastBurstStartFrame = i;
                state.burstStart = true;
            }

            // --- 4Ca. Tracking Burst Evolution ---
            if (state.burstStart && (i == state.lastBurstStartFrame + static_cast<int>(framesPerSec * 0.005 * locCounter)) && (locCounter < capacity)) {
                locs[locCounter] = sensor.getWindow()->getAvgX();
                burstSpikeCounts[locCounter] = spikeCount;
                locCounter++;
            }

            // --- 4Cb. Detect Sig Burst is happening ---
            // --- This is for turning off stimulation during a burst ---
            if (waveVal == Wave::bursting){
                state.bursting = true;
                directionHandled = false;
            }

            // --- 4D. Handle Burst End ---
            else if ((waveVal == Wave::burstOnLeft || waveVal == Wave::burstOnRight) && !directionHandled) {
                
                bool burstStartLeft = (waveVal == Wave::burstOnLeft);
                string directionString = burstStartLeft ? "burst on Left" : "burst on Right";
                cout << "Burst END: " << directionString << endl;

                state.previousBurst = burstStartLeft ? 1 : -1;  // 1 is Left, -1 is Right
                state.bursting = false;
                directionHandled = true;

                WaveMetadata metadata = sensor.getMetadata();
                saveBurstData(metadata, file, locs, burstSpikeCounts, capacity, framesPerSec, SYS_START_BUFFER, WINDOW, directionString);
                sensor.resetBurstMetadata();  // Reset the burst metadata after saving

                //expBar.clear();
                //expBar.print();
            }
        }

        // === 5. Handle Stimulation if Necessary ===
        // the python file passes 0 for none, 1 for regular, 2 for random.
        bool stimulate = false;
        if (state.previousBurst == -1) {
            stimulate = rightStim.stimulate(i);
            // // Debug
            // if (stimulate == 1){
            //     cout << "rightStim stimulate is: " << stimulate << endl;
            // }
            
        } else if (state.previousBurst == 1) {
            stimulate = leftStim.stimulate(i);
            // // Debug
            // if (stimulate == 1){
            //     cout << "leftStim stimulate is: " << stimulate << endl;
            // }
        }
        
        // // Debug statement
        // if (stimulate == 1){
        //     cout << "stimulate: " << stimulate 
        //     << " | bursting: " << state.bursting << endl;
        // }

        if (stimulate && !state.bursting && state.blanking == 0) {
            cout << "PULSE" << endl;
            maxlab::verifyStatus(maxlab::sendSequence(("pulse" + to_string(well)).c_str()));
            state.blanking = BLANKING_FRAMES; // Restart blanking after stimulation
        }
    }

    // =====================================================
    //                     Post-Training Phase
    // =====================================================
    cout << BOLD << CYAN << "\n===== End of Training =====" << RESET << endl;
    cout << left << setw(15) << (YELLOW + "Recording:") << RESET << framesToSeconds(post_frames, framesPerSec) / 60.0 << (YELLOW + " minutes of neuron activity") << endl;
    ProgressBar postBar = ProgressBar(post_frames, "Recording...");

    // This line send an event to mark the end of training in the raw data
    maxlab::verifyStatus(maxlab::sendSequence(("post_recording_start_" + to_string(well)).c_str()));    

    // The actual loop that goes through 'post_frames'
    for (int i = 0; i < post_frames; i++) {
        maxlab::FilteredFrameData frameData;
        maxlab::Status status = maxlab::DataStreamerFiltered_receiveNextFrame(&frameData);
        if (status == maxlab::Status::MAXLAB_NO_FRAME) {
            i--;        // Retry if no good frame
            continue;
        }

        // Important in alpha - don't process all frames
        if (frameData.frameInfo.well_id != well) {
            i--;  // don't advance if wrong well
            continue;
        }

        postBar.increment();
    }
    cout << endl;

    // =====================================================
    //                     Closing Phase
    // =====================================================
    cout << BOLD << CYAN << "\n===== END OF EXPERIMENT =====" << RESET << endl;
    cout << left << setw(15) << (YELLOW + "Now closing files safely...") << endl;
    maxlab::verifyStatus(maxlab::DataStreamerFiltered_close());
    file.close();
    alldata_file.close();
}

