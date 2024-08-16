#include "progressBar.h"

using namespace std;

ProgressBar::ProgressBar() {
    initVars(50, "");
}

ProgressBar::ProgressBar(int numTasks, string description, bool debug) {
    initVars(numTasks, description, debug);
}



void ProgressBar::increment() {
    tasksComplete++;
    progress = tasksComplete / (float) totalTasks;
    float tickRatio = currentTick / (float) totalTicks;
    if (progress > tickRatio) {
        bar[currentTick] = '#';
        currentTick++;
        if (printBar) {
            clear();
            print();
        }
        
    }
    
}

void ProgressBar::print() {
    if (printBar) {
        cout << "[";
        for (int i = 0; i < 50; i++) {
            cout << bar[i] << flush;
        }

        int percent = progress * 100;

        // 5 represents brackets, 2 spaces, and percent sign
        numCharacters = totalTicks + 5 + countDigits(percent) + desc.length();

        cout << "] " << percent << "% " << desc << flush;
    }
    

}

void ProgressBar::clear() {
    if (printBar) {
        cout << "\r" << string(numCharacters, ' ') << "\r" << flush;
    }
    
}

void ProgressBar::initVars(int numTasks, string description, bool debug) {
    for (int i = 0; i < 50; i++) {
        bar.push_back('.');
    }

    currentTick = 0;
    desc = description;
    totalTicks = 50;
    progress = 0;
    totalTasks = numTasks;
    tasksComplete = 0;
    printBar = !debug;

    numCharacters = totalTicks + 5 + desc.length();
}

int ProgressBar::countDigits(int number) {
    int count = 1;
    while (number > 9) {
        count++;
        number = number / 10;
    }

    return count;
}