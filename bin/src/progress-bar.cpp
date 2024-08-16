#include <iostream>
#include <ncurses.h>
#include <unistd.h>
#include "hal.h"

using namespace std;

void printBarRaw(char bar[]) {
    cout << "\r[";
    for (int i = 0; i < 50; i++) {
        cout << bar[i];
    }

     cout << "]";
}

int main()
{
    int numTasks = 500;
    ProgressBar bar = ProgressBar(numTasks, "Experiment Progress");
    string end = string(65, ' ');

    for (int i = 0; i < numTasks; i++) {
        bar.increment();
        usleep(100000);
        bar.clear();
        cout << "something " << i << endl;
        bar.print();
    }

    cout << endl;
}

