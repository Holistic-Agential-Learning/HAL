#include "nes.h"
#include <iostream>
#include <fstream>
#include "maxlab.h"

NES::NES(float spikePercentThreshold, float zScoreThreshold) {
    percentThresh = spikePercentThreshold;
    zThresh = zScoreThreshold;
}

NES::NES(const char *csvName, float spikePercentThreshold, float zScoreThreshold) {
    cout << "Opening csv "  << csvName << endl;
    csv.open(csvName, std::fstream::out);

    if (csv.is_open()) {
        // put header in csv
        csv << "frame number, button pressed, percent fired A, firing rate A, avg FR A, SD A, Z score A, percent fired B, firing rate B, avg FR B, SD B, Z Score B" << endl;
    } else {
        cerr << __FILE__ << ":\n\tError: could not open file " << csvName << endl;
    }

    NES(spikePercentThreshold, zScoreThreshold);
}

NES::NES(bool maxtwo, int windowLength, const char *AconfigPath, const char *BconfigPath, const char *csvName, float spikePercentThreshold, float zScoreThreshold) {
    cout << "Initializing NES controller" << endl;
    int framesPerSec = maxtwo ? 10000 : 20000;

    // saves 5 seconds of past window data to compare against
    int numPastWindows = (framesPerSec * 5) / windowLength;
    cout << "Number of past windows to save: " << numPastWindows << endl;

    addButton("A", windowLength, AconfigPath, numPastWindows);
    addButton("B", windowLength, BconfigPath, numPastWindows);

    NES(csvName, spikePercentThreshold, zScoreThreshold);
}

NES::~NES() {
    if (csv.is_open()) csv.close();
}

// void NES::addButton(string id, int windowLength, const char *configPath, int saveWindows) override {
//     if (numButtons == 2) {
        
//     }
// }