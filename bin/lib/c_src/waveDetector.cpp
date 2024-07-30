#include "waveDetector.h"

// #define MEM_ERR() {\
//     cerr << "Error (" << __FILE__ << ", " << __LINE__ << ": memory allocation failed." << endl;\
//     exit(1);\
// }

WaveDetector::WaveDetector() {

}

WaveDetector::WaveDetector(int numLocations, int windowLength, const char *configPath, float threshold, int minFrames, int frameHz) {
    ChannelWindow *window = new ChannelWindow(windowLength, configPath);

    ElectrodeMap emap = window->electrodeMap();

    threshold = threshold;
    framesPerSec = frameHz;
    minFrames = minFrames;
    totalElectrodes = emap.size();

    metadata = calloc(1, sizeof(WaveMetadata));

    if (metadata == NULL) {
        cerr << "metadata memory allocation failed." << endl;
        exit(1);
    }

    // metaData->firstBurstDone = false;

    // metaData->spikeFrameCount = 0;

    // metaData->burstStartFrame= 0;
    // metaData->burstStartSpikeCount = 0;
    // metaData->burstStartLocation = 0;
    // metaData->burstEnd = 0;

    // metaData->noSpikeFrameCount = 0;

    // metaData->maxSpikesFrame = 0;
    // metaData->maxSpikes = 0;

    // metaData->maxSpikesLoc = 0;

    // metaData->bursting = false;
}

WaveDetector::~WaveDetector() {
    delete window;
    free(metadata);
}

void WaveDetector::shiftWindow(maxlab::FilteredFrameData frame) {
    window->shift(frame);
}

void WaveDetector::checkBurst(int frameNo) {
    int spikeCount = window->totalSpikeCount();

    // spike in activity
    if  (spikeCount > threshold * totalElectrodes) { 
        if (!metadata->bursting) {
            // burst started
            metadata->bursting = true;

            metadata->burstStartLocation = window.getAvgX(); 
            metadata->burstStartSpikeCount = spikeCount;
            metadata->burstStartFrame = frameNo;
        }

        // what does 0.005 represent?
        if (!metadata->firstBurstDone && spikeCount > metadata->maxSpikes && frameNo % (int)(framesPerSec * 0.005) == 0){
            metadata->maxSpikes = spikeCount;
            metadata->maxSpikesFrame = frameNo;
            metadata->maxSpikesLoc = window.getAvgX();
        }
        
        metadata->spikeFrameCount++; // spike at this frame
        metadata->noSpikeFrameCount = 0;

    // no spike in activity
    } else { 

        // 0.2?
        if (!firstBurstDone && metadata->noSpikeFrameCount > 0.2 * framesPerSec) {
            metadata->firstBurstDone = true; 
        }

        // burst is over
        if (metadata->noSpikeFrameCount > 0.2 * framesPerSec) {
            
            metadata->bursting = false;
            
            // burst is long enough to be significant
            if (spikeFrameCount >= minFrames) {
                
                int leftToRight = metadata->burstStartLocation < metadata->maxSpikesLoc;
                string locString = leftToRight ? "left to right" : "right to left";
                          
            }      
            metadata->firstBurstDone = false;
            metadata->maxSpikes = 0;  
            metadata->spikeFrameCount = 0;
        }
        noSpikeFrameCount++;
    }
}