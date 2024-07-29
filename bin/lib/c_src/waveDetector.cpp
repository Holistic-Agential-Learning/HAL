#include "waveDetector.h"

WaveDetector::WaveDetector() {

}

WaveDetector::WaveDetector(int windowLength, const char *configPath, float threshold, int frameHz) {
    ChannelWindow *window = new ChannelWindow(windowLength, configPath);

    ElectrodeMap emap = window->electrodeMap();

    totalElectrodes = emap.size();
    this->threshold = threshold;

    framesPerSec = frameHz;

    spikeFrameCount = 0;

    burstStart = 0;
    burstEnd = 0;

    noSpikeFrameCount = 0;

    firstBurstDone = false;
    maxSpikesFrame = 0;
    maxSpikes = 0;

    maxSpikesLoc = 0;
    locCounter = 0;
    monitoringLoc = 0;

    previousBurstInDesiredDirection = 0;
    bursting = false;
}

WaveDetector::~WaveDetector() {
    delete window;
}

void WaveDetector::shiftWindow(maxlab::FilteredFrameData frame) {
    window->shift(frame);
}

// void WaveDetector::checkBurst() {
//     int spikeCount = window->totalSpikeCount();

//     if  (spikeCount > threshold * totalElectrodes) {
//         if (!bursting) {
//             bursting = true;
//             cout << "burst started" << endl;

//             locs[0] = window.getAvgX(); // starting location
//             burstSpikeCounts[0] = spikeCount;
//             locCounter = 1;
//             burstStart = i;
//         }

//         if (!firstBurstDone && spikeCount > maxSpikes && i % (int)(framesPerSec * 0.005) == 0){
//             maxSpikes = spikeCount;
//             maxSpikesFrame = i;
//             maxSpikesLoc = window.getAvgX();
//         }
        
//         spikeFrameCount++; // spike at this frame
//         noSpikeFrameCount = 0;
//     } else {
//         if (!firstBurstDone && noSpikeFrameCount > 0.2 * framesPerSec) {
//             firstBurstDone = true; 
//         }

//         // burst is over
//         if (noSpikeFrameCount > 0.2 * framesPerSec) {
            
//             bursting = false;
//             // burst is long enough to be significant
//             if (spikeFrameCount >= MIN_FRAMES) {
                
//                 // // edge case: startingLocDiff = 0 (right for now)
//                 int left_to_right = locs[0] < maxSpikesLoc;
//                 string loc_string = left_to_right ? "left to right" : "right to left";
//                 cout << loc_string << endl;
//                 file <<"BURST" << endl;
//                 for(int m = 0; m < capacity; m++) {
//                     file << burstStart + SYS_START_BUFFER + WINDOW + m * (int)(framesPerSec * 0.01) << ", ";
//                 }
//                 file << maxSpikesFrame + SYS_START_BUFFER + WINDOW;

//                 file << endl;
                
//                 for(int m = 0; m < capacity; m++) {
//                     file << locs[m] << ", ";
//                 }
//                 file << maxSpikesLoc << ", ";

//                 file << loc_string << endl;
//                 for(int m = 0; m < capacity; m++) {
//                     file << burstSpikeCounts[m] << ", ";
//                 }
//                 file << maxSpikes;
                
//                 file << endl;       

//                 previousBurstInDesiredDirection = left_to_right;             
//             }      
//             firstBurstDone = false;
//             maxSpikes = 0;  
//             spikeFrameCount = 0;
//         }
//         noSpikeFrameCount++;
//     }
// }