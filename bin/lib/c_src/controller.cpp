#include "controller.h"
#include <utility>

Controller::Controller() {
}

Controller::~Controller() {
    for (const auto& pair: buttons) {
        string key = pair.first;
        ChannelWindow *win = buttons[key];
        delete win;
    }
}

void Controller::addButton(const char *configPath, string id, int windowLength) {
    ChannelWindow *win = new ChannelWindow(windowLength, configPath);

    buttons.insert(make_pair(id, win));
}

ChannelWindow *Controller::getButtonWindow(string id) {
    ChannelWindow *win = buttons[id];

    return win;
}

void Controller::add(maxlab::FilteredFrameData frame) {

    for (const auto& pair: buttons) {
        string key = pair.first;
        ChannelWindow *win = buttons[key];
        win->add(frame);
    }
}

void Controller::shift(maxlab::FilteredFrameData frame) {
    for (const auto& pair: buttons) {
        string key = pair.first;
        ChannelWindow *win = buttons[key];
        win->shift(frame);
    }
}

int Controller::numChannels(string id) {
    ChannelWindow *cw = buttons[id];

    ElectrodeMap emap = cw->electrodeMap();

    return emap.size();
}

int Controller::numSpikes(string id) {
    ChannelWindow *cw = buttons[id];

    return cw->totalSpikeCount();
}