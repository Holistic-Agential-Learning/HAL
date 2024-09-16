#include "channelWindow.h"
#include <map>
#include <string>

#ifndef __CONTROLLER_H__
#define __CONTROLLER_H__

using namespace std;


class Controller {
    public:

        /**
         * @brief Construct a new Controller object
         * 
         */
        Controller();

        /**
         * @brief Destroy the Controller object
         * 
         */
        ~Controller();

        /**
         * @brief Adds a new button (ChannelWindow) to the Controller 
         * 
         * @param id <code>string</code> identifier of the button/config
         * @param windowLength <code>int</code> length of the window
         * @param configPath <code>char</code> array representing the full path 
         *                  of the config file
         * @param saveWindows <code>int</code> indicating how many windows to 
         *                  save, default 0
         */
        void addButton(string id, int windowLength, const char *configPath, int saveWindows=0);

        /**
         * @brief Initializes all buttons
         * 
         */
        void init();
         

        /**
         * @brief Get the ChannelWindow of the specified button
         * 
         * @param id <code>string</code> id of the button
         * @return pointer to a <code>ChannelWindow</code>
         * @throws <code>std::out_of_range</code> if there is not a button with 
         *         the key <code>id</code>
         */
        ChannelWindow *getButtonWindow(string id);

        /**
         * @brief checks if a button exists in the controller
         * 
         * @param id <code>string</code> id of the button
         * @return true 
         * @return false 
         */
        bool buttonExists(string id);

        /**
         * @brief Adds a data frame to all button windows
         * 
         * Note that this function will extend the window, not shift it
         * 
         * @param frame <code>maxlab::FilteredFrameData</code> frame to add to 
         *              each window
         */
        void add(maxlab::FilteredFrameData frame);

        /**
         * @brief Shifts all button windows--the first frame of each window will
         *        be removed, and a new one will be appended to the end.
         * 
         * @param frame <code>maxlab::FilteredFrameData</code> frame to add to 
         *              each window
         */
        void shift(maxlab::FilteredFrameData frame);

        /**
         * @brief Gets the number of channels tracked by a button
         * 
         * @param id <code>string</code> id of the button
         * @return <code>int</code>
         */
        int numChannels(string id);

        /**
         * @brief Gets the number of spikes in the window of a button
         * 
         * @param id <code>string</code> id of the button
         * @return <code>int</code>
         */
        int numSpikes(string id);

    private:
        map<string, ChannelWindow *> buttons;

        int getMaxLength();
};

#endif