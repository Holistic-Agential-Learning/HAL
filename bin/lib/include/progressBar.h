#include <vector>
#include <iostream>
#include <stdlib.h>
#include <string>

#ifndef __PROGRESSBAR_H__
#define __PROGRESSBAR_H__

using namespace std;

class ProgressBar {
    public:
        ProgressBar();

        ProgressBar(int numTasks, string description);

        void increment();

        void print();

        void clear();

    private:
        int totalTicks;
        int currentTick;
        int totalTasks;
        int tasksComplete;
        float progress;
        int numCharacters;
        
        vector<char> bar;
        string desc;

        void initVars(int numTasks, string description);
        int countDigits(int number);


};
#endif