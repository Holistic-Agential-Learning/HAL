#include "channelWindow.h"

using namespace maxlab;

ChannelWindow::ChannelWindow(int length, ElectrodeMap electrodeMap) {
    emap = electrodeMap;
    size = length;
}

void ChannelWindow::add(maxlab::FilteredFrameData frame) {
    const SpikeEvent * spikeEvents = frame.spikeEvents;
    int spikeCount = frame.spikeCount;
    int newSpikeCount = 0;
    for (int i = 0; i < spikeCount; i++) {
        newSpikeCount += addEvent(spikeEvents[i]);
    }
    frame.spikeCount = newSpikeCount;
    window.push_back(frame);
}

void ChannelWindow::shift(maxlab::FilteredFrameData frame) {
    sum -= window[0].spikeCount;
    window.erase(window.begin());
    add(frame);
}

FilteredFrameData ChannelWindow::get(int idx) {
    if (idx >= size || idx < 0) {
        exit(1);
    }

    return window[idx];
}

int ChannelWindow::length() {
    return size;
}

int ChannelWindow::totalSpikeCount() {
    return sum;
}

ElectrodeMap ChannelWindow::electrodeMap() {
    return emap;
}

int ChannelWindow::addEvent(maxlab::SpikeEvent se) {
    if (emap.exists(se.channel)) {
        cout << "activity detected from channel " << se.channel << endl;
        sum++;
        return 1;
    }

    return 0;
}