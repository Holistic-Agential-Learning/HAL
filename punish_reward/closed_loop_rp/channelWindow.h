#include <string>
#include <electrodeMap.h>
#include <vector>
#include <maxlab.h>
#include <stdlib.h>
#include <iostream>
#include <map>

#ifndef __CHANNELWINDOW_H__
#define __CHANNELWINDOW_H__

using namespace std;

class ChannelWindow {
    public:

        /* Constructor
         * 
         * Creates a new ChannelWindow
         * 
         * Parameters:
         *      - length: integer representing the length of the window 
         *                (measured in frames)
         *      - emap: ElectrodeMap holding the current electrode config file
         */
        ChannelWindow(int length, ElectrodeMap emap);

        /* add
         * 
         * Adds a data frame to the window, and increment the total spike sum 
         * accordingly. The sum will only be incremented for each channel in 
         * frame that exists in the electrode map.
         * 
         * Parameters:
         *      - frame: FilteredFrameData struct to add to the window
         * 
         * Side effects: updates frame.spikeCount to count only the existing
         *               channel numbers
         */
        void add(maxlab::FilteredFrameData frame);


        /* shift
         * 
         * "Shifts" the window by removing the first frame (and updating the 
         * total sum accordingly), and adding the new frame to the end. Similar
         * to add, the sum will only be incremented for each channel in frame 
         * that exists in the electrode map.
         * 
         * Parameters:
         *      - frame: FilteredFrameData struct to add to the window
         * 
         * Side effects: updates frame.spikeCount
         */
        void shift(maxlab::FilteredFrameData frame);

        /* get
         * 
         * gets a FilteredFrameData struct at the specified index
         * 
         * Parameters:
         *      - idx: integer representing the index of the target frame
         * 
         * Returns: FilteredFrameData struct at the specified index within the 
         *          window
         */
        maxlab::FilteredFrameData get(int idx);

        /* length
         * 
         * Returns the length of the window
         * 
         * Returns: integer representing the length of the window
         * 
         */
        int length();

        /* totalSpikeCount
         * 
         * Returns the sum of all the spike counts (of valid channels) in the 
         * window.
         * 
         * Returns: integer representing the sum of all spike counts
         */
        int totalSpikeCount();

        /* electrodeMap
         * 
         * Returns the emap.
         * 
         * Returns: ElectrodeMap containing all of the channel, electrode 
         *          mappings
         */
        ElectrodeMap electrodeMap();

        void print();
    
    private:
        vector<maxlab::FilteredFrameData> window;
        ElectrodeMap emap;
        int size;
        int sum;

        /* addEvent
         * 
         * Increments sum if the given SpikeEvent channel exists in emap
         * 
         * Parameters:
         *      - se: SpikeEvent struct to check
         * 
         * Returns: integer indicating if the SpikeEvent channel exists (1 if
         *          true, false otherwise)
         */
        int addEvent(maxlab::SpikeEvent se);



};

#endif