#include "stimVector.h"
#include <stdlib.h>
#include <iostream>

using namespace std;

StimVector::StimVector(bool isRandom, int stimRate, bool maxtwo, float interval, float shuffleFrequency) {
    // TODO: check bounds 
    random = isRandom;
    stimsPerSec = stimRate;
    fps = maxtwo ? 10000 : 20000;
    framesPerStim = (1.0 / stimRate) * fps;
    intvl = interval * fps;
    length = (shuffleFrequency * fps) / intvl;
    
    stims = (int *) calloc(length, sizeof(int));

    leftover = 0;

    if (random) {
        generateRandom();
    }
}

int StimVector::stimulate(int frame) {
    if (random) {
        if (frame % (length * intvl) == 0) {
            generateRandom();
        }
        if (frame % 10 == 0) {
            int stim = (frame % (intvl * length)) / intvl;
            cout << stim << endl;
            return stims[stim];
        } else {
            return 0;
        }
    } else {
        if (stimsPerSec == 0) {
            return 0;
        } else {
            return ((frame % framesPerStim) == 0);
        }
    }
}

void StimVector::generateRandom() {
    free(stims);
    stims = (int *) calloc(length, sizeof(int));
    stimIdxs.clear();
    int numStims = stimsPerSec * (length * intvl / fps);

    while (stimIdxs.size() < numStims) {
        int randInt = rand() % length;
        if (!stimIdxs.count(randInt)) {
            /* v does not contain x */
            stimIdxs[randInt] = true;
            stims[randInt] = 1;
        }
    }
}

StimVector::~StimVector() {
    if (random) {
        free(stims);
    }
}