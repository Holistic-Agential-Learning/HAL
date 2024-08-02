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

/**
 * Add description for the <code>ChannelWindow</code> class
 */
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
        
        // assumes that the data streamer is open
        void init();


        /**
         * @brief Adds a data frame to the window.
         * 
         * Adds only the <code>maxlab::spikeEvents</code> that are found in the given 
         * config or <code>ElectrodeMap</code>, and increments the total spike sum 
         * accordingly. 
         * 
         * @param frame <code>maxlab::FilteredFrameData</code> struct to add to 
         *              the window
         * 
         * @return None
         * 
         */
        void add(maxlab::FilteredFrameData frame);

        

        /**
         * @brief Shifts window, appending new data frame to the end
         * 
         * Shifts the window by removing the first frame, updating the 
         * total sum accordingly, and adding the new frame to the end. Similar
         * to add, the sum will only be incremented for each channel in frame 
         * that exists in the electrode map. Note that it will only count the 
         * <code>maxlab::spikeEvents</code> that are found in the given config
         * 
         * @param frame <code>maxlab::FilteredFrameData</code> struct to add to 
         *              the window
         */
        void shift(maxlab::FilteredFrameData frame);

        /**
         * @brief Gets a <code>maxlab::FilteredFrameData</code> struct at the 
         *          specified index
         * 
         * @param idx <code>int</code> representing the index of the target frame
         * 
         * @return <code>maxlab::FilteredFrameData</code> struct at the 
         *          specified index within the window
         */
        maxlab::FilteredFrameData get(int idx);

        /**
         * @brief Returns the length of the window
         * 
         * @return <code>int</code> representing the length of the window
         */
        int length();

        /**
         * @brief  Returns the sum of all the spike counts (of valid channels) 
         *          in the window
         * 
         * @return <code>int</code> representing the sum of all spike counts
         * 
         */
        int totalSpikeCount();

        /**
         * @brief Returns the <code>ElectrodeMap</code>
         * 
         * @returns <code>ElectrodeMap</code> containing all of the channel, 
         *          electrode mappings
         */
        ElectrodeMap electrodeMap();

        /**
         * @brief Gets a vectors containing the firing rates of all the past 
         *          windows
         * 
         * @return <code>vector<float></code> 
         */
        vector<float> pastWindows();

        /**
         * @brief Returns the average firing rate of all the past windows
         * 
         * @return <code>float</code>
         */
        float avgPastWindows();

        /**
         * @brief Computes the average x coordinate of all the spike events in 
         *          the window
         * 
         * @return <code>float</code> 
         */
        float getAvgX();
        
        /**
         * @brief Computes the standard deviation of the firing rates of all 
         *          past windows
         * 
         * @return <code>float</code>
         */
        float firingRateSD();

        /**
         * @brief Computes the firing rate of the window
         * 
         * @return <code>float</code>
         */
        float firingRate();

        /**
         * @brief Indicates whether the window is completely unique from the 
         *          past windows
         * 
         * The past windows are stored end-to-end, so, at any point in time, 
         * there is a high chance that the current window overlaps with the past
         * ones. When this function returns true, the current window does *not 
         * overlap* with any of the previous windows, and will be counted in all 
         * computations relating to the past windows.
         * 
         * @return <code>bool</code>
         */
        bool pastWindowsReady();

        /**
         * @brief Prints the ChannelWindow
         * 
         */
        void print();

        /**
         * @brief Prints the window with a message
         * 
         * Also counts each spike event in the window manually, and compares it 
         * to the recorded sum
         * 
         * @param message <code>string</code> to print
         */
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