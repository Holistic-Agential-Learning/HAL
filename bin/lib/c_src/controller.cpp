#include "controller.h"
#include <utility>
#include <maxlab.h>
#include <iostream>

Controller::Controller() {
}

Controller::~Controller() {
    cout << "freeing buttons" << endl;
    for (const auto& pair: buttons) {
        delete pair.second;
    }
}

void Controller::addButton(string id, int windowLength, const char *configPath, int saveWindows) {
    ChannelWindow *win = new ChannelWindow(windowLength, configPath, saveWindows);

    if (buttons.count(id) > 0) {
        ChannelWindow *old = buttons.at(id);
        delete old;
    }
    buttons.insert(make_pair(id, win));
}

void Controller::init() {
    int maxLength = getMaxLength();

    for (int i = 0; i < maxLength; i++) {
        maxlab::FilteredFrameData frameData;
        maxlab::Status status = maxlab::DataStreamerFiltered_receiveNextFrame(&frameData);

        if (status == maxlab::Status::MAXLAB_NO_FRAME) {
            i--;
            continue;
        }

        for (const auto& pair: buttons) {
            ChannelWindow *button = pair.second;
            if (i + button->length() > maxLength) {
                button->add(frameData);
            }
        }
    }
}

int Controller::getMaxLength() {
    int max = 0;
    for (const auto& pair: buttons) {
        int buttonLength = pair.second->length();
        if (buttonLength > max) {
            max = buttonLength;
        }
    }

    return max;
}

ChannelWindow *Controller::getButtonWindow(string id) {
    ChannelWindow *win = buttons.at(id);

    return win;
}

bool buttonExists(string id) {
    return buttons.count();
}

void Controller::add(maxlab::FilteredFrameData frame) {

    for (const auto& pair: buttons) {
        (pair.second)->add(frame);
    }
}

void Controller::shift(maxlab::FilteredFrameData frame) {
    for (const auto& pair: buttons) {
        (pair.second)->shift(frame);
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