#include <vector>
#include <iostream>
#include <stdlib.h>

#ifndef __PROGRESSBAR_H__
#define __PROGRESSBAR_H__

class ProgressBar {
    public:
        ProgressBar();

        void increment();

        void printBar();

    private:
        int current;
        vector<char> bar;


};
#endif