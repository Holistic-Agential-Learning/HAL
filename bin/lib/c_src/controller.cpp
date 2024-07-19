#include "controller.h"

Controller::Controller() {

}

void Controller::addButton(const char *configPath, string id, int windowLength) {
    ChannelWindow win = ChannelWindow(windowLength, configPath);

    struct Button b;
    b.win = win;

    map.at(id) = b;
}

ChannelWindow Controller::getButtonWindow(string id) {
    Button b = map[id];

    return b.win;
}

void Controller::add(maxlab::FilteredFrameData frame) {
    for (auto& b: map) {
        b.win.add(frame);
    }
}

void Controller::shift(maxlab::FilteredFrameData frame) {
    for (auto& b: map) {
        b.win.shift(frame);
    }
}