#include "waveDetector.h"

// #define MEM_ERR() {\
//     cerr << "Error (" << __FILE__ << ", " << __LINE__ << ": memory allocation failed." << endl;\
//     exit(1);\
// }
WaveDetector::WaveDetector() {

}

WaveDetector::WaveDetector(int windowLength, const char *configPath, float threshold, int minFrames, int frameHz, float firstBurstThreshold, float burstDoneThreshold) {
    window = new ChannelWindow(windowLength, configPath);

    window->init();

    ElectrodeMap emap = window->electrodeMap();

    this->threshold = threshold;
    framesPerSec = frameHz;
    this->minFrames = minFrames;
    this->firstBurstThreshold = firstBurstThreshold;
    this->burstDoneThreshold = burstDoneThreshold;
    totalElectrodes = emap.size();

    metadata = (WaveMetadata *)calloc(1, sizeof(WaveMetadata));

    if (metadata == NULL) {
        cerr << __FILE__ << " line " << __LINE__ << ": metadata memory allocation failed." << endl;
        exit(1);
    }
}

WaveDetector::~WaveDetector() {
    delete window;
    free(metadata);
}

ChannelWindow *WaveDetector::getWindow() {
    return window;
}

WaveMetadata WaveDetector::getMetadata() {
    return *metadata;
}

void WaveDetector::shiftWindow(maxlab::FilteredFrameData frame) {
    window->shift(frame);
}



int WaveDetector::checkBurst(int frameNo) {

    int ret = Wave::noBurst;
    int spikeCount = window->totalSpikeCount();


    // spike in activity
    if  (spikeCount > threshold * totalElectrodes) { 
        ret = Wave::bursting;

        // NOTE: needs more logic here
        if (!metadata->bursting) {
    
            // burst started
            metadata->bursting = true;

            metadata->burstStartLocation = window->getAvgX(); 
            metadata->burstStartSpikeCount = spikeCount;
            metadata->burstStartFrame = frameNo;

            ret = Wave::burstStart;
        }



        // TODO: add variable for 0.005
        if (!metadata->firstBurstDone && spikeCount > metadata->maxSpikes && frameNo % (int)(framesPerSec * 0.005) == 0){
            metadata->maxSpikes = spikeCount;
            metadata->maxSpikesFrame = frameNo;
            metadata->maxSpikesLoc = window->getAvgX();
        }
        
        metadata->spikeFrameCount++; // spike at this frame
        metadata->noSpikeFrameCount = 0;

    // no spike in activity
    } else { 

        // TODO: add variable for 0.2
        if (!metadata->firstBurstDone && metadata->noSpikeFrameCount > firstBurstThreshold * framesPerSec) {
            metadata->firstBurstDone = true; 
        }

        // TODO: add another variable for 0.2
        // burst is over
        if (metadata->noSpikeFrameCount > burstDoneThreshold * framesPerSec) {
            
            metadata->bursting = false;
            
            // burst is long enough to be significant
            if (metadata->spikeFrameCount >= minFrames) {
                
                bool startLeft = metadata->burstStartLocation < metadata->maxSpikesLoc;
                if (startLeft) {
                    ret = Wave::leftToRight;
                } else {
                    ret = Wave::rightToLeft;
                }

            } else {
                ret = Wave::endShortBurst;
            }

            metadata->firstBurstDone = false;
            metadata->maxSpikes = 0;  
            metadata->spikeFrameCount = 0;
        }
        metadata->noSpikeFrameCount++;
    }

    return ret;
}

int WaveDetector::processFrame(maxlab::FilteredFrameData frame, int frameNo) {
    if (window == NULL) {
        cerr << __FILE__ << " line " << __LINE__ << ": window is NULL" << endl;
        exit(1);
    }
    window->shift(frame);

    return checkBurst(frameNo);
}