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
    ProgressBar bar = ProgressBar("Experiment Progress");
    string end = string(65, ' ');

    for (int i = 0; i < 50; i++) {
        bar.increment();
        usleep(100000);
        cout << "\r" << "something " << i << end << endl;
        bar.print();
    }

    cout << endl;
}

