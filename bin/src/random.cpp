#include <iostream>
#include <stdlib.h>
#include <time.h>
#include "hal.h"


using namespace std;

int main(int argc, char *argv[]) {
    srand(time(NULL));
    StimVector v = StimVector(1, 5, true);

    for (int i = 0; i < 200000; i++) {
        int stim = v.stimulate(i);
        if (stim) {
            cout << i << endl;
        }
    }
} 