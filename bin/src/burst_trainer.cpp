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
#include <unistd.h>
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
#define RANDOM_SEED 10  /* fixed random seed */
#define SYS_START_BUFFER 5 * FRAMES_PER_SEC /* The system takes ~ 5 secs to startup */
#define TOTAL_ELECTRODES emap.size()        /* So you know how many electrodes there are for thresholds */
#define CHIP_WIDTH 220  /* This is how many electrodes in X (L/R will use CHIP_WIDTH / 2) */
#define CHIP_HEIGHT 120 /* This is how many electrodes in Y */

// THESE ARE REALLY IMPORTANT /////////////////////////////////////////

// This will set how long ChannelWindow is in frames
// (ChannelWindow collects spikesrates over the window)
#define WINDOW 0.01 * FRAMES_PER_SEC    /* 100 frames ~ 10 ms for M2 */

// A burst will ONLY count if it lasts more than this
// Keep in mind that FRAMES_PER_SEC changes on M1 and M2
#define MIN_FRAMES 0.1 * FRAMES_PER_SEC /* 1000 frames ~ 100 ms for M2 */

// As it's written above, with a WINDOW of 10 ms and a MIN_FRAMES at 1000,
// a window will signal a high firing rate, and if it stays high for long
// enough, the 'burststart' trigger should flip. 

//////////////////////////////////////////////////////////////////////////

// DEFAULTS - WILL MOST LIKELY BE REPLACED BY INPUT FROM USER 
// VIA THE PYTHON FILE. This is the way. 

#define THRESHOLD_DEFAULT 0.15      /* activity burst threshold */
#define PRE_MINUTES_DEFAULT 20      /* 20 min */
#define TRAIN_MINUTES_DEFAULT 20    /* 20 min */
#define POST_MINUTES_DEFAULT 20     /* 20 min */

#define STIM_RATE_DEFAULT 5 /* 5 Hz (stims per second) */
#define RANDOM_WINDOW_GEN_TIME 5 /* generate randomness over 5 second intervals */

////////////////////////////////////////////////////
////////// PROTOTYPES AND ^C ///////////////////////
////////////////////////////////////////////////////

//  Some quick function setup (called prototypes)
//  They provide the compiler with information about the signature of the functions;
//  what types of arguments they take, and what type they return.

// Converts frames to seconds b/c it's easier sometimes
float framesToSeconds(int frames);
// This function actually holds the experimental logic (aka the meat)
void runExperiment(string path, string configPath, int framesPerSec, int preFrames, int frames, int postFrames,
    int well, float threshold, int pollingWindowSize,
    int rightStimType, int leftStimType);

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

    string folderPath = getStringArg("--folder", argc, argv, USAGE);     // This sets where saving happens 
    string configPath = getStringArg("--config", argc, argv, USAGE);     // Where is your config
    
    float threshold = getFloatArgSecure("--threshold", THRESHOLD_DEFAULT, argc, argv);  // What's considered a burst (% of channels)
    bool maxtwo = checkOption("--maxtwo", argc, argv);  // Are you using a MaxTwo or not
    int well = getIntArgSecure("--well", 0, argc, argv);    // Which well are you going to work on
    
    // --- Set sampling rate based on device type ---
    int framesPerSec = maxtwo ? 10000 : 20000;

    // --- This will set flags for the stimulation behavior --- 
    // --- default: right == random, left == nothing
    int leftburst = getIntArgSecure("--right-type", 2, argc, argv);   // stimulation for leftburst
    int rightburst = getIntArgSecure("--left-type", 0, argc, argv);    // stimulation for rightburst

    // Stimulation parameters
    float stimRate = getFloatArgSecure("--stim-rate", STIM_RATE_DEFAULT, argc, argv);   // Stim rate in Hz
    float pulseDurationSecs = getFloatArgSecure("--pulse-duration", 0.0002, argc, argv);    // How long a pulse is (duration is 2 times this)
    
    // Timing parameters
    float train_mins = getFloatArgSecure("--minutes", MINUTES_DEFAULT, argc, argv); // How long you want training to last
    float pre_mins = getIntArgSecure("--pre-recording", 5, argc, argv); // How long you want pre training to last
    float post_mins = getIntArgSecure("--post-recording", 5, argc, argv);   // How long you want post training to last
    float total_time = pre_mins + train_mins + post_mins;

    // Print pretty things
    cout << BOLD << CYAN << "\n===== Experiment Setup =====" << RESET << endl;
    cout << left << setw(15) << (YELLOW + "Device:")     << RESET << "Max" << (maxtwo ? "TWO" : "ONE") << endl;
    cout << left << setw(15) << (YELLOW + "Config:")     << RESET << configPath << endl;
    cout << left << setw(15) << (YELLOW + "Threshold:")  << RESET << threshold << endl;
    cout << left << setw(15) << (YELLOW + "Well:")       << RESET << well << endl;
    cout << left << setw(15) << (YELLOW + "Pretrain:")   << RESET << pre_mins << " mins" << endl;
    cout << left << setw(15) << (YELLOW + "Training:")   << RESET << train_mins << " mins" << endl;
    cout << left << setw(15) << (YELLOW + "Posttrain:")  << RESET << post_mins << " mins" << endl;
    cout << left << setw(15) << (YELLOW + "Total time:") << RESET << GREEN << total_time << " mins" << RESET << endl;
    cout << BOLD << CYAN << "=============================\n" << RESET << endl;

    ElectrodeMap emap = ElectrodeMap(configPath.c_str());


}
