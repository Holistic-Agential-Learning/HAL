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

        ProgressBar(string description);

        void increment();

        void print();

    private:
        int current;
        vector<char> bar;
        string desc;


};
#endif