#include "channelWindow.h"

using namespace maxlab;

ChannelWindow::ChannelWindow(int length, ElectrodeMap electrodeMap) {
    emap = electrodeMap;
    size = length;
}

void ChannelWindow::add(maxlab::FilteredFrameData frame) {
    const SpikeEvent * spikeEvents = frame.spikeEvents;
    int spikeCount = frame.spikeCount;
    for (int i = 0; i < spikeCount; i++) {
        if (emap.exists(spikeEvents[i].channel)) {
            sum++;
        }
    }
    window.push_back(frame);
}

void ChannelWindow::shift(maxlab::FilteredFrameData frame) {
    FilteredFrameData firstFrame = window[0];
    const SpikeEvent * spikeEvents = firstFrame.spikeEvents;
    int spikeCount = firstFrame.spikeCount;
    for (int i = 0; i < firstFrame.spikeCount; i++) {
        if (emap.exists(spikeEvents[i].channel)) {
            sum--;
        }
    }
    if (sum < 0) {
        cerr << "CHANNEL WINDOW IS ABOUT TO BE NEGATIVE" << endl;
        cerr << "Before shifting: " << endl;
        print()
    }
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

void ChannelWindow::print() {
    cerr << "Printing window ----------------------------" << endl;
    cerr << "Sum: " << endl;
    for (int i = 0; i < size; i++) {
        maxlab::FilteredFrameData fd = get(i);
        cerr << "Index " << i << endl;
        cerr << "Spike count: " << fd.spikeCount << endl;
        maxlab::SpikeEvent * spikeEvents = fd.spikeEvents;
        int spikeCount = fd.spikeCount;
        for (int j = 0; j < spikeCount; j++) {
            maxlab::SpikeEvent se = spikeEvents[j];
            cerr << "\tFrame: " << se.frameNo << endl;
        }
    }
}

int ChannelWindow::addEvent(maxlab::SpikeEvent se) {
    if (emap.exists(se.channel)) {
        // cout << "activity detected from channel " << se.channel << endl;
        sum++;
        return 1;
    }

    return 0;
}