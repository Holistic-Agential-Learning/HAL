#include "stimVector.h"
#include <stdlib.h>
#include <iostream>

using namespace std;

StimVector::StimVector(bool isRandom, int stimRate, bool maxtwo, float interval, float shuffleFrequency) {
    // TODO: check bounds 
    random = isRandom;
    stimsPerSec = stimRate;
    fps = maxtwo ? 10000 : 20000;
    framesPerStim = stimRate ? (1.0 / stimRate) * fps : 0;
    intvl = interval * fps;
    length = (shuffleFrequency * fps) / intvl;
    
    stims = (bool *) calloc(length, sizeof(bool));

    if (random) {
        generateRandom();
    }
}

bool StimVector::stimulate(int frame) {
    if (random) {
        if (frame % (length * intvl) == 0) {
            generateRandom();
        }
        if (frame % 10 == 0) {
            int stim = (frame % (intvl * length)) / intvl;
            return stims[stim];
        } else {
            return false;
        }
    } else {
        if (stimsPerSec == 0) {
            return false;
        } else {
            return ((frame % framesPerStim) == 0);
        }
    }
}

void StimVector::generateRandom() {
    free(stims);
    stims = (bool *) calloc(length, sizeof(bool));
    stimIdxs.clear();
    int numStims = stimsPerSec * (length * intvl / fps);

    while (stimIdxs.size() < numStims) {
        int randInt = rand() % length;
        if (!stimIdxs.count(randInt)) {
            /* v does not contain x */
            stimIdxs[randInt] = true;
            stims[randInt] = true;
        }
    }
}

StimVector::~StimVector() {
    if (random) {
        free(stims);
    }
}