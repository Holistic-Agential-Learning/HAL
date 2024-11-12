
#include <map>

using namespace std;

class StimVector {

    public:

        /**
         * @brief Construct a new Stim Vector object
         * 
         * @param isRandom <code>bool</code> indicates whether the object should
         * simulate a random or regular stimulation pattern 
         * @param stimRate <code>int</code> stimulation rate in stimulations 
         * per second; must be >= 0 and <= FPS, default <code>5</code>
         * @param maxtwo <code>bool</code> indicates if the program is running 
         * on the maxtwo, default <code>false</code>
         * @param interval <code>float</code> space between "bins" for shuffling,
         * in seconds, default <code>0.001</code>
         * @param shuffleFrequency <code>float</code> length of shuffle window, 
         * in seconds, default <code>5</code>
         */
        StimVector(bool isRandom=true, int stimRate=5, bool maxtwo=false, float interval=0.001, float shuffleFrequency=5);

        ~StimVector();

        bool stimulate(int frame);

    private:
        // machine (Mx1 or Mx2) frame/sample rate
        int fps;
        
        // indicates if stimulation is random or regular
        bool random;
        
        // stimulations per second
        int stimsPerSec;

        // number of frames in between each stimulation (for regular)
        int framesPerStim;
        
        // how often to check for stimulation, in frames
        int intvl;

        // length of window (for re-rolling random stimulations)
        int length;

        // array for random stimulations
        bool *stims;

        /* keeps track of which indices have been chosen for stimulation for 
        random generation */
        map<int, bool> stimIdxs;

        void generateRandom();
};
