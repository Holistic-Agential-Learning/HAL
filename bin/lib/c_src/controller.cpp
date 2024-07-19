#include "controller.h"

Controller::Controller() {

}

void Controller::addButton(const char *configPath, string id, int windowLength) {
    struct Button b;
    b.win = ChannelWindow(windowLength, configPath);

    buttons[id] = b;
}

ChannelWindow Controller::getButtonWindow(string id) {
    struct Button b = buttons[id];

    return b.win;
}

void Controller::add(maxlab::FilteredFrameData frame) {
    for (map<string, struct Button>::iterator it = buttons.begin(); 
            it != buttons.end(); it++) {
        string key = it->first;
        struct Button b = buttons[key];
        b.win.add(frame);
    }
}

// void Controller::shift(maxlab::FilteredFrameData frame) {
//     for (auto& b: buttons) {
//         b.second.win.shift(frame);
//     }
// }