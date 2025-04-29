#ifndef __STIMVECTOR_H__
#define __STIMVECTOR_H__

#include <vector>
#include <unordered_map>
#include <random>

using namespace std;

/**
 * @class StimVector
 * @brief Manages the logic for generating stimulation patterns (random or regular).
 *
 * Supports regular evenly-spaced stimulations or randomized stimulations,
 * including automatic refreshing of random patterns over long experiments.
 */
class StimVector {

    public:
        /**
         * @brief Construct a new Stim Vector object
         * 
         * @param isRandom <code>bool</code> If true, generates randomized stimulations.
         * @param stimRate <code>int</code> Stimulations per second; must be >= 0.
         *                 Use <code>0</code> to disable stimulation entirely.
         * @param maxtwo <code>bool</code> True if running on MaxTwo (10kHz), false for MaxOne (20kHz).
         * @param interval <code>float</code> Duration of a randomization bin, in seconds (default 0.001s).
         * @param shuffleFrequency <code>float</code> How often (in seconds) to refresh the random stimulation pattern (default 5s).
         * 
         * @note If <code>stimRate</code> is 0, the stimulator will remain inactive regardless of mode.
         */
        StimVector(bool isRandom = true, int stimRate = 5, bool maxtwo = false, float interval = 0.001, float shuffleFrequency = 5);

        /**
         * @brief Destroy the Stim Vector object
         */
        ~StimVector();

        /**
         * @brief Determines whether a pulse should be sent at the given frame.
         * 
         * @param frame <code>int</code> The current frame index.
         * @return <code>bool</code> True if a stimulation pulse should occur, false otherwise.
         */
        bool stimulate(int frame);

    private:

        /**
         * @brief Internal helper to generate or regenerate random stimulation pattern.
         */
        void generateRandom();

        // machine (Mx1 or Mx2) frame/sample rate
        int fps;
        
        // indicates if stimulation is random or regular
        bool random;
        
        // stimulations per second
        int stimsPerSec;

        // number of frames in between each stimulation (for regular mode)
        int framesPerStim;
        
        // duration of each randomization bin, in frames
        int intvl;

        // number of bins (length of random stimulation vector)
        int length;

        // how many frames between random stimulation re-generation
        int framesUntilNextShuffle;

        // array for storing random stimulation flags
        std::vector<bool> stims;

        // keeps track of which indices have been chosen for random generation
        std::unordered_map<int, bool> stimIdxs;

        // random number generator
        std::mt19937 randomEngine;
};

#endif
