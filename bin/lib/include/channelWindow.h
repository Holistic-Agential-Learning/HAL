#include <string>
#include <electrodeMap.h>
#include <vector>
#include <maxlab.h>
#include <stdlib.h>
#include <iostream>
#include <fstream>
#include <map>

#ifndef __CHANNELWINDOW_H__
#define __CHANNELWINDOW_H__

using namespace std;


class ChannelWindow {
    public:

        ChannelWindow();

        /**
         * @brief Constructor
         * 
         * Creates a new ChannelWindow object
         * 
         * @param length <code>int</code> representing the length of the window 
         *                (measured in frames)
         * @param configPath <code>char</code> array representing the full path 
         *                  of the config to use for the underlying ElectrodeMap
         * @param toSave <code>int</code> indicating how many past window 
         *              firing rates are to be saved, default=0
         */
        ChannelWindow(int length, const char* configPath, int toSave=0);


        /**
         * @brief Constructor 
         * 
         * Creates a new ChannelWindow object
         * 
         * @param length <code>int</code> representing the length of the window 
         *                (measured in frames)
         * @param emap <code>ElectrodeMap</code> holding the current electrode 
         *              config file
         * @param toSave <code>int</code> indicating how many past window 
         *              firing rates are to be saved, default=0
         */
        ChannelWindow(int length, ElectrodeMap emap, int toSave=0);
        


        /**
         * @brief Adds a data frame to the window.
         * 
         * Adds only the <code>maxlab::spikeEvents</code> that are found in the given 
         * config or <code>ElectrodeMap</code>, and increments the total spike sum 
         * accordingly. 
         * 
         * @param frame FilteredFrameData struct to add to the window
         * 
         * @return None
         * 
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

        vector<float> pastWindows();

        float avgPastWindows();

        float getAvgX();
        float stdDev();
        float firingRate();

        bool pastWindowsReady();

        void print();
        void debug(string message);
    
    private:
        vector<maxlab::FilteredFrameData> spikeWindow;
        ElectrodeMap emap;
        int size;
        int sum;

        bool savesWindows;
        int numPastWindows;
        vector<float> pastData;

        int newWindowCount;
        

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

        void shiftOrAdd(maxlab::FilteredFrameData frame);
        void addFrame(maxlab::FilteredFrameData frame);
        void shiftFrame(maxlab::FilteredFrameData frame);



};

#endif