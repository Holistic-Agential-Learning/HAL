#include <iostream>
#include <stdlib.h>
#include <time.h>
#include "hal.h"


using namespace std;

int main(int argc, char *argv[]) {
    srand(time(NULL));
    StimVector v = StimVector(false, 5, true);

    for (int i = 0; i < 200000; i++) {
        bool stim = v.stimulate(i);
        if (stim) {
            cout << i << endl;
        }
    }
} 