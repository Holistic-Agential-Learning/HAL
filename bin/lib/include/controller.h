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

        ~Controller();

        void addButton(string id, int windowLength, const char *configPath, int saveWindows=0);

        ChannelWindow *getButtonWindow(string id);

        void add(maxlab::FilteredFrameData frame);

        void shift(maxlab::FilteredFrameData frame);

        int numChannels(string id);

        int numSpikes(string id);

    private:
        map<string, ChannelWindow *> buttons;
};

#endif