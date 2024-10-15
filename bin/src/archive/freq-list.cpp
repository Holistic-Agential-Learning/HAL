#include "hal.h"
#include <string>
#include <iostream>
#include <fstream>
#include <vector>

using namespace std;
using namespace argparse;

// grabs floats from string, comma separated
vector<float> parseFloats(string floatList) {
    size_t startIdx = 0;
    size_t target = 0;
    vector<float> freqs;
    while ((target = floatList.find(",", startIdx)) != string::npos) {
        string value = floatList.substr(startIdx, target);
        startIdx = target + 1;
        freqs.push_back(stof(value.c_str()));
    } 

    freqs.push_back(stof(floatList.substr(startIdx, target).c_str()));

    return freqs;

}

vector<float> getFrequencies(int argc, char *argv[]) {
    bool isFile = checkOption("--stim-freq-file", argc, argv);
    string freqString = "";

    if (isFile) {
        // read from file
        string freqFile = getStringArg("--stim-freq-file", argc, argv);
        ifstream file;

        file.open(freqFile.c_str());
        if (!file.is_open()) {
            cerr << "Error: failed to open " << freqFile << endl;
            exit(1);
        }

        getline(file, freqString);

    } else {
        // from the command line or nonexistent
        freqString = getStringArg("--stim-freqs", argc, argv, "blunk");
    }

    return parseFloats(freqString);
}

int main(int argc, char *argv[]) {
    vector<float> freqs = getFrequencies(argc, argv);

    cout << "[ ";

    for (auto f: freqs) {
        cout << f << " ";
    }
    cout << "]" << endl;
}