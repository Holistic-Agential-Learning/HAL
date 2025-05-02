#include "stimVector.h"
#include <iostream>
#include <random>
#include <chrono>

using namespace std;

/**
 * @brief Construct a new Stim Vector object
 * 
 * @param isRandom <code>bool</code> indicates whether the object should simulate a random or regular stimulation pattern 
 * @param stimRate <code>int</code> stimulation rate in stimulations per second
 * @param fps fps <code>int</code> frames per sec (10k for M2 and 20k)
 * @param interval <code>float</code> size of each random bin in seconds (default 0.001)
 * @param shuffleFrequency <code>float</code> how often (in seconds) to regenerate the random pattern (default 5)
 */
StimVector::StimVector(bool isRandom, int stimRate, int fps, float interval, float shuffleFrequency)
    : random(isRandom), stimsPerSec(stimRate), shuffleFrequency(shuffleFrequency)
{
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

    // cout << "[StimVector] frame = " << frame << ", framesPerStim = " << framesPerStim
    //  << ", frame % fps: " << (frame % framesPerStim) << endl;

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
            bool shouldStim = (frame % framesPerStim) == 0;
            // // Debug
            // if (shouldStim) {
            //     std::cout << "[StimVector] 🔥 SHOULD STIMULATE at frame = " << frame
            //               << ", framesPerStim = " << framesPerStim
            //               << ", frame % fps: " << frame % fps << std::endl;
            // }
            return shouldStim;  // <-- THIS WAS MISSING, LOL
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
    int numStims = static_cast<int>(stimsPerSec * shuffleFrequency);

    uniform_int_distribution<int> dist(0, length - 1);

    while (stimIdxs.size() < static_cast<size_t>(numStims)) {
        int randIdx = dist(randomEngine);
        if (stimIdxs.insert(randIdx).second) {
            stims[randIdx] = true;
        }
    }

    // // Quick debug
    // std::cout << "[StimVector] Generated stim vector (first 100 bins): ";
    // for (int i = 0; i < std::min(100, length); ++i) {
    //     std::cout << stims[i];
    // }
    // std::cout << std::endl;
}

/**
 * @brief Destroy the Stim Vector object
 * 
 * Handles any necessary cleanup (none required in this version).
 */
StimVector::~StimVector() {
    // No manual memory management needed
}
