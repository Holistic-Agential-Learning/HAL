/**
 * @file progressBar.h
 * @author Trevor Sullivan (trevor.sullivan@tufts.edu)
 * @brief Header file for the ProgressBar Class
 * @version 0.1
 * @date 2024-09-18
 * 
 * @copyright Copyright (c) 2024
 * 
 */

#ifndef __PROGRESSBAR_H__
#define __PROGRESSBAR_H__

#include <vector>
#include <string>

using namespace std;

class ProgressBar {
    public:
        ProgressBar();

        ProgressBar(int numTasks, string description, bool debug=false);

        void increment();

        void print();

        void clear();

        int numTasksComplete();

        float getProgress();

    private:
        int totalTicks;
        int currentTick;
        int totalTasks;
        int tasksComplete;
        float progress;
        int numCharacters;
        bool printBar;
        
        vector<char> bar;
        string desc;

        void initVars(int numTasks, string description,  bool debug=false);
        int countDigits(int number);


};
#endif