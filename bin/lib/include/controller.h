#include "channelWindow.h"
#include <map>
#include <string>

#ifndef __CONTROLLER_H__
#define __CONTROLLER_H__

using namespace std;


class Controller {
    public:

        Controller();

        ~Controller();

        void addButton(const char *configPath, string id, int windowLength);

        ChannelWindow *getButtonWindow(string id);

        void add(maxlab::FilteredFrameData frame);

        void shift(maxlab::FilteredFrameData frame);

        int numChannels(string id);

        int numSpikes(string id);

    private:
        map<string, ChannelWindow *> buttons;
};

#endif