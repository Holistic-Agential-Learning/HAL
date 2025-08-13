#include "stimVector.h"
#include <iostream>
#include <random>
#include <chrono>
#include <cmath>      // for rounding
#include <set>        // for set
#include <numeric>    // for iota
#include <algorithm>  // for shuffle

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
    // Frames per stimulus (≥ 1 if stimRate > 0)
    if (stimRate > 0) {
        framesPerStim = std::max(1, static_cast<int>(std::lround((1.0 / stimRate) * fps)));
    } else {
        framesPerStim = 0;
    }

    // Convert times → frames with rounding, not truncation
    const int framesPerShuffle = std::max(1, static_cast<int>(std::lround(shuffleFrequency * fps)));
    intvl = std::max(1, static_cast<int>(std::lround(interval * fps)));

    // length = ceil(framesPerShuffle / intvl) using integers
    length = std::max(1, (framesPerShuffle + intvl - 1) / intvl);

    framesUntilNextShuffle = framesPerShuffle;

    stims.assign(length, false);

    randomEngine.seed(std::chrono::system_clock::now().time_since_epoch().count());
    if (random) generateRandom();
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
            //     cout << "[StimVector] 🔥 SHOULD STIMULATE at frame = " << frame
            //               << ", framesPerStim = " << framesPerStim
            //               << ", frame % fps: " << frame % fps << endl;
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
    fill(stims.begin(), stims.end(), false);
    stimIdxs.clear();

    int numStims = static_cast<int>(stimsPerSec * shuffleFrequency);

    // Step 1: Generate a shuffled list of all possible indices
    vector<int> candidates(length);
    iota(candidates.begin(), candidates.end(), 0); // Fill with 0...length-1
    shuffle(candidates.begin(), candidates.end(), randomEngine);

    // Step 2: Pick candidates with spacing >= 3
    set<int> selected;
    for (int idx : candidates) {
        bool tooClose = false;
        for (int offset = -2; offset <= 2; ++offset) {
            if (offset == 0) continue;
            if (selected.count(idx + offset)) {
                tooClose = true;
                break;
            }
        }
        if (!tooClose) {
            selected.insert(idx);
            stims[idx] = true;
            if (static_cast<int>(selected.size()) == numStims)
                break;
        }
    }

    // Final check
    if (static_cast<int>(selected.size()) < numStims) {
        cerr << "[StimVector] Warning: Only " << selected.size()
                  << " stimulations placed out of requested " << numStims
                  << " due to spacing constraints.\n";
    }
    
    // Optional: Debug output
    // cout << "[StimVector] Generated stim vector (first 100 bins): ";
    // for (int i = 0; i < min(100, length); ++i) {
    //     cout << stims[i];
    // }
    // cout << endl;
}


/**
 * @brief Destroy the Stim Vector object
 * 
 * Handles any necessary cleanup (none required in this version).
 */
StimVector::~StimVector() {
    // No manual memory management needed
}
