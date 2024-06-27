#include "hal.h"
#include <iostream>

using namespace std;

int main(int argc, char * argv[]) {

    int minutes = getIntArg("--time", argc, argv);
    float threshold = getFloatArg("--threshold", argc, argv);
    bool isMaxTwo = checkOption("--maxtwo", argc, argv);
    string configPath = getStringArg("--config", argc, argv);

    cout << "Running experiment on Max" << (isMaxTwo ? "Two" : "One") << " for " << minutes << " minutes." << endl;
    cout << "Threshold: " << threshold << endl;
    cout << "Config: " << configPath << endl;
}
