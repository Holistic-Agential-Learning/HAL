#include "nes.h"
#include <iostream>
#include <fstream>
#include "maxlab.h"

NES::NES(float spikePercentThreshold, float zScoreThreshold) {
    percentThresh = spikePercentThreshold;
    zThresh = zScoreThreshold;
    cout << "Z score theshold: " << zThresh << endl << "P thresh: " << percentThresh << endl;
    aReleased = true;
    bReleased = true;
}

NES::NES(const char *csvName, float spikePercentThreshold, float zScoreThreshold) {
    cout << "Opening csv "  << csvName << endl;
    csv.open(csvName, std::fstream::out);

    if (csv.is_open()) {
        // put header in csv
        csv << "frame number, button pressed, percent fired A, firing rate A, avg FR A, SD A, Z score A, percent fired B, firing rate B, avg FR B, SD B, Z Score B" << endl;
    } else {
        cerr << "Error in " << __FILE__ << ": could not open file " << csvName << endl;
        exit(1);
    }

    percentThresh = spikePercentThreshold;
    zThresh = zScoreThreshold;
    cout << "Z score theshold: " << zThresh << endl << "P thresh: " << percentThresh << endl;
    aReleased = true;
    bReleased = true;
}

NES::NES(bool maxtwo, int windowLength, const char *AconfigPath, const char *BconfigPath, const char *csvName, float spikePercentThreshold, float zScoreThreshold) {
    cout << "Initializing NES controller" << endl;
    int framesPerSec = maxtwo ? 10000 : 20000;

    // saves 5 seconds of past window data to compare against
    int numPastWindows = (framesPerSec * 5) / windowLength;
    cout << "Number of past windows to save: " << numPastWindows << endl;

    addButton("A", windowLength, AconfigPath, numPastWindows);
    addButton("B", windowLength, BconfigPath, numPastWindows);

    cout << "Opening csv "  << csvName << endl;
    csv.open(csvName, std::fstream::out);

    if (csv.is_open()) {
        // put header in csv
        csv << "frame number, button pressed, percent fired A, firing rate A, avg FR A, SD A, Z score A, percent fired B, firing rate B, avg FR B, SD B, Z Score B" << endl;
    } else {
        cerr << "Error in " << __FILE__ << ": could not open file " << csvName << endl;
        exit(1);
    }

    percentThresh = spikePercentThreshold;
    zThresh = zScoreThreshold;
    cout << "Z score theshold: " << zThresh << endl << "P thresh: " << percentThresh << endl;
    aReleased = true;
    bReleased = true;
}

NES::~NES() {
    if (csv.is_open()) csv.close();
}

int NES::checkButtons(int frameNo) {
    if (!(buttonExists("A") && buttonExists("B"))) return -1;
    
    ChannelWindow *winA = getButtonWindow("A");
    ChannelWindow *winB = getButtonWindow("B");

    bool aPressed = false;
    bool bPressed = false;

    int buttonPressed = 0;

    if (winA->pastWindowsReady() && winB->pastWindowsReady()) {
        float firingRateAvgA = winA->avgPastWindows();
        float firingRateAvgB = winB->avgPastWindows();
        float sdA = winA->firingRateSD();
        float sdB = winB->firingRateSD();
        float firingRateA = winA->firingRate();
        float firingRateB = winB->firingRate();
        float zScoreA = zScore(firingRateA, firingRateAvgA, sdA);
        float zScoreB = zScore(firingRateB, firingRateAvgB, sdB);
        int spikeCountA = winA->totalSpikeCount();
        int spikeCountB = winB->totalSpikeCount();

        int numChannelsA = winA->numChannels();
        int numChannelsB = winB->numChannels();

        float percentChannelsFiredA = spikeCountA / (float) numChannelsA;
        float percentChannelsFiredB = spikeCountB / (float) numChannelsB;

        bool aPressed = false;
        bool bPressed = false;

        // Button A was pressed
        if (aReleased && bReleased && zScoreA > zThresh && percentChannelsFiredA > percentThresh) {
            aPressed = true;
        // Button B was pressed 
        } 
        if (aReleased && bReleased && zScoreB > zThresh && percentChannelsFiredB > percentThresh) {
            bPressed = true;
        } 

        // check if the button is currently being "pressed"
        aReleased = !aPressed;
        bReleased = !bPressed;

        // ensure that only A or B gets pressed
        if (aPressed && bPressed) {
            if (percentChannelsFiredA >= percentChannelsFiredB) {
                bPressed = false;
            } else aPressed = false;
        }

        if (aPressed) {
            buttonPressed = 1;
        } else if (bPressed) buttonPressed = 2;

        if (csv.is_open()) {
            printValues(buttonPressed, frameNo, percentChannelsFiredA, firingRateA, firingRateAvgA, sdA, zScoreA, percentChannelsFiredB, firingRateB, firingRateAvgB, sdB, zScoreB);
        }
    }

    return buttonPressed;
}

bool NES::abExist() {
    return buttonExists("A") && 
}

void NES::printValues(int ab, int frameNo, float perA, float valA, float avgA, float sdA, float zA, float perB, float valB, float avgB, float sdB, float zB) {
    csv << frameNo << ", " << ab << ", " ;
    csv << perA << ", "<< valA << ", " << avgA << ", " << sdA << ", " << zA << ", ";
    csv << perB << ", "<< valB << ", " << avgB << ", " << sdB << ", " << zB << endl;
}

float NES::zScore(float value, float avg, float sd) {
    return (value - avg) / sd;
}