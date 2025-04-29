#include "stimVector.h"
#include <iostream>
#include <random>
#include <chrono>

using namespace std;

/**
 * @brief Construct a new Stim Vector object
 * 
 * @param isRandom <code>bool</code> indicates whether the object should
 * simulate a random or regular stimulation pattern 
 * @param stimRate <code>int</code> stimulation rate in stimulations per second
 * @param maxtwo <code>bool</code> indicates if running on MaxTwo (true) or MaxOne (false)
 * @param interval <code>float</code> size of each random bin in seconds (default 0.001)
 * @param shuffleFrequency <code>float</code> how often (in seconds) to regenerate the random pattern (default 5)
 */
StimVector::StimVector(bool isRandom, int stimRate, bool maxtwo, float interval, float shuffleFrequency)
    : random(isRandom), stimsPerSec(stimRate)
{
    fps = maxtwo ? 10000 : 20000;
    framesPerStim = stimRate ? static_cast<int>((1.0 / stimRate) * fps) : 0;
    intvl = interval * fps;
    length = static_cast<int>((shuffleFrequency * fps) / intvl);

    framesUntilNextShuffle = static_cast<int>(shuffleFrequency * fps);

    stims.resize(length, false);

    // Setup random generator
    randomEngine.seed(chrono::system_clock::now().time_since_epoch().count());

    if (random) {
        generateRandom();
    }
}

/**
 * @brief Check if a stimulation pulse should be sent on this frame
 * 
 * @param frame <code>int</code> current frame index
 * @return <code>bool</code> true if a pulse should be sent, false otherwise
 */
bool StimVector::stimulate(int frame) {
    if (random) {
        // Regenerate the random stimulation pattern periodically
        if (frame % framesUntilNextShuffle == 0 && frame != 0) {
            generateRandom();
        }

        // Check if current frame aligns with a stimulation bin
        if (frame % static_cast<int>(intvl) == 0) {
            int stimIndex = (frame % (length * intvl)) / static_cast<int>(intvl);
            return stims[stimIndex];
        } else {
            return false;
        }
    } else {
        // Regular stimulation mode (even spacing)
        if (stimsPerSec == 0) {
            return false;
        } else {
            return (frame % framesPerStim) == 0;
        }
    }
}

/**
 * @brief Randomly generate a new stimulation pattern
 * 
 * Fills the stims vector with random stimulation events, 
 * based on the requested stimulation rate and shuffle frequency.
 */
void StimVector::generateRandom() {
    fill(stims.begin(), stims.end(), false); // Reset all bins to false

    stimIdxs.clear();
    int numStims = static_cast<int>(stimsPerSec * (length * intvl / fps));

    uniform_int_distribution<int> dist(0, length - 1);

    while (stimIdxs.size() < static_cast<size_t>(numStims)) {
        int randIdx = dist(randomEngine);
        if (!stimIdxs.count(randIdx)) {
            stimIdxs[randIdx] = true;
            stims[randIdx] = true;
        }
    }
}

/**
 * @brief Destroy the Stim Vector object
 * 
 * Handles any necessary cleanup (none required in this version).
 */
StimVector::~StimVector() {
    // No manual memory management needed
}
