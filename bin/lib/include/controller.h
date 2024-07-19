#include "channelWindow.h"
#include <map>
#include <string>

#ifndef __CONTROLLER_H__
#define __CONTROLLER_H__

using namespace std;

struct Button {
    ChannelWindow win;
}

class Controller {
    public:

        Controller();   

        void addButton(const char *configPath, string id, int windowLength);

        ChannelWindow getButtonWindow(string id);

        void add(maxlab::FilteredFrameData frame);

        void shift(maxlab::FilteredFrameData frame)


    private:
        map<string, struct Button> buttons;
};

#endif