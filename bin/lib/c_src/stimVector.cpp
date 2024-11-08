#include "stimVector.h"
#include <stdlib.h>
#include <iostream>

using namespace std;

StimVector::StimVector(int type, int stimRate, bool maxtwo, float interval, float shuffleFrequency) {
    // TODO: check bounds 
    stimType = type;
    stimsPS = stimRate;
    fps = maxtwo ? 10000 : 20000;
    intvl = interval * fps;
    length = shuffleFrequency * fps;
    
    stims = (int *) calloc(length, sizeof(int));

    leftover = 0;

    if (stimType) {
        generateRandom();
    } 
}

int StimVector::stimulate(int frame) {
    if (frame % length * intvl == 0) {
        if (stimType) {
            generateRandom();
        }
    }
    if (frame % 10 == 0) {
        return stims[(frame % (intvl * length)) / intvl];
    } else {
        return 0;
    }
}

void StimVector::generateRandom() {
    //length >> numStims.
    free(stims);
    stims = (int *) calloc(length, sizeof(int));
    stimIdxs.clear();
    int numStims = stimsPS * (length / fps);

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
    free(stims);
}