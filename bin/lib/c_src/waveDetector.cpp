#include "waveDetector.h"

// #define MEM_ERR() {\
//     cerr << "Error (" << __FILE__ << ", " << __LINE__ << ": memory allocation failed." << endl;\
//     exit(1);\
// }

WaveDetector::WaveDetector() {

}

WaveDetector::WaveDetector(int windowLength, const char *configPath, float threshold, int minFrames, int frameHz) {
    ChannelWindow *window = new ChannelWindow(windowLength, configPath);

    ElectrodeMap emap = window->electrodeMap();

    threshold = threshold;
    framesPerSec = frameHz;
    minFrames = minFrames;
    totalElectrodes = emap.size();

    metadata = (WaveMetadata *)calloc(1, sizeof(WaveMetadata));

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

        // what does 0.005 represent? potentially add else
        if (!metadata->firstBurstDone && spikeCount > metadata->maxSpikes && frameNo % (int)(framesPerSec * 0.005) == 0){
            metadata->maxSpikes = spikeCount;
            metadata->maxSpikesFrame = frameNo;
            metadata->maxSpikesLoc = window->getAvgX();
        }
        
        metadata->spikeFrameCount++; // spike at this frame
        metadata->noSpikeFrameCount = 0;

    // no spike in activity
    } else { 

        // 0.2?
        if (!metadata->firstBurstDone && metadata->noSpikeFrameCount > 0.2 * framesPerSec) {
            metadata->firstBurstDone = true; 
        }

        // burst is over
        if (metadata->noSpikeFrameCount > 0.2 * framesPerSec) {
            
            metadata->bursting = false;
            
            // burst is long enough to be significant
            if (metadata->spikeFrameCount >= minFrames) {
                
                int startLeft = metadata->burstStartLocation < metadata->maxSpikesLoc;
                if (startLeft) {
                    ret = Wave::leftToRight;
                } else {
                    ret = Wave::rightToLeft;
                }
            } else {
                ret = endShortBurst;
            }

            metadata->firstBurstDone = false;
            metadata->maxSpikes = 0;  
            metadata->spikeFrameCount = 0;
        }
        metadata->noSpikeFrameCount++;
    }

    return ret;
}