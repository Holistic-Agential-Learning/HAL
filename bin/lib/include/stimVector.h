


class StimVector {

    public:

        /**
         * @brief Construct a new Stim Vector object
         * 
         * @param type <code>int</code> vector type: 0 for regular, and and 
         *              anything else for random, default <code>1</code>
         * @param stimRate <code>int</code> stimulation rate in stimulations 
         *                 per second; must be >= 0 and <= FPS, default <code>5</code>
         * @param maxtwo <code>bool</code> indicates if the program is running 
         *                  on the maxtwo, default <code>false</code>
         * @param interval <code>float</code> space between "bins" for shuffling,
         *                  in seconds, defaul <code>0.001</code>
         * @param shuffleFrequency <code>float</code> length of shuffle window, 
         *                          in seconds, default <code>5</code>
         */
        StimVector(int type=1, int stimRate=5, bool maxtwo=false, float interval=0.001, float shuffleFrequency=5);

    private:

        int type;
        int stimsPS;
        int *stims;
};
