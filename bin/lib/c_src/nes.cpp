#include "nes.h"
#include <iostream>
#include <fstream>
#include "maxlab.h"

NES::NES(float spikePercentThreshold, float zScoreThreshold) {
    percentThresh = spikePercentThreshold;
    zThresh = zScoreThreshold;
}

NES::NES(const char *csvName, float spikePercentThreshold, float zScoreThreshold) {
    csv.open(csvName, std::fstream::out);

    NES(spikePercentThreshold, zScoreThreshold);
}

NES::NES(const char *AconfigPath, const char *BconfigPath, int windowLength, const char *csvName, bool maxtwo, float spikePercentThreshold, float zScoreThreshold) {
    int framesPerSec = maxtwo ? 10000 : 20000;

    // saves 5 seconds of past window data to compare against
    int numPastWindows = (framesPerSec * 5) / windowLength;

    addButton("A", windowLength, AconfigPath, numPastWindows);
    addButton("B", windowLength, BconfigPath, numPastWindows);

    NES(csvName, spikePercentThreshold, zScoreThreshold);
}

void NES::addButton(string id, int windowLength, const char *configPath, int saveWindows) override {
    if (numButtons == 2) {
        
    }
}