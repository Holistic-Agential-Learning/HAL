#include "channelWindow.h"
#include <fstream>

using namespace maxlab;

ChannelWindow::ChannelWindow(int length, ElectrodeMap electrodeMap) {
    emap = electrodeMap;
    size = length;
    sum = 0;
}

void ChannelWindow::add(maxlab::FilteredFrameData frame) {
    const maxlab::SpikeEvent *spikeEvents = frame.spikeEvents;
    int spikeCount = frame.spikeCount;
    int numValid = 0; // number of channels found in the config
    for (int i = 0; i < spikeCount; i++) {
        if (emap.exists(spikeEvents[i].channel)) {
            sum++;
            numValid++;
        }
    }

    // copy over spike events that have channel numbers in the config
    if (numValid > 0) {
        maxlab::SpikeEvent *newSpikeEvents = (maxlab::SpikeEvent *)malloc(numValid * sizeof(maxlab::SpikeEvent));
        int newSpikeEventsIdx = 0;
        for (int i = 0; i < spikeCount; i++) {
            if (emap.exists(spikeEvents[i].channel)) {
                maxlab::SpikeEvent temp = spikeEvents[i];
                newSpikeEvents[newSpikeEventsIdx] = temp;
                newSpikeEventsIdx++;
            }
        }
        frame.spikeEvents = newSpikeEvents;
    }

    frame.spikeCount = numValid;
    
    window.push_back(frame);
}

void ChannelWindow::shift(maxlab::FilteredFrameData frame) {
    maxlab::FilteredFrameData firstFrame = window[0];
    const maxlab::SpikeEvent *spikeEvents = firstFrame.spikeEvents;
    int spikeCount = firstFrame.spikeCount;
    // int beforeSum = sum;
    // for (int i = 0; i < spikeCount; i++) {
    //     if (emap.exists(spikeEvents[i].channel)) {
    //         sum--;
    //     }
    // }
    sum -= spikeCount;
    if (spikeCount > 0) {
        free((void *)firstFrame.spikeEvents);
    }
    window.erase(window.begin());
    // if (beforeSum != sum) {
    //     debug("Removing frame with a positive spikeCount:");
    // }
    // beforeSum = sum;
    add(frame);

    // if (beforeSum != sum) {
    //     debug("Adding VALIDATED with positive spikeCount:");
    // } else if (frame.spikeCount > 0) {
    //     debug("Adding INVALID frame with positive spikeCount");
    // }
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

float ChannelWindow::getAvgX() {

    // used to make sure that each channel is only counted once
    int channels[1024];
    float avgSum = 0;
    float count = 0;
    for (int i = 0; i < size; i++) {
        FilteredFrameData fd = get(i);
        const SpikeEvent *event = fd.spikeEvents;
        int spikeCount = fd.spikeCount;
        for (int j = 0; j < spikeCount; j++) {
            // compute column coordinate and add to sum
            int channel = event[j].channel;
            // if the channel has already been counted
            if (channels[channel] == 0) {
                float x_coord = emap.get_x(channel);
                avgSum += x_coord;
                channels[channel] = 1;
                count++;
            }
            
        }
    }
    float average = avgSum / count;
    if (sum > 0 && avgSum == 0 && count == 0) {
        cout << "average is nan, sum is " << sum << endl;  
        debug("average is nan");
    }
    return average;
}

void ChannelWindow::debug(string message) {
    std::fstream file;
    file.open("ERR_LOG", std::fstream::out | std::fstream::app);
    file << "Debugging window ----------------------------" << endl;
    file << message << endl;
    file << "Size: " << size << endl;
    file << "Window Length: " << window.size() << endl;
    file << "Sum: " << sum << endl;
    int tempSum = 0;
    for (int i = 0; i < window.size(); i++) {
        maxlab::FilteredFrameData fd = get(i);
        file << "Index " << i << endl;
        file << "Spike count: " << fd.spikeCount << endl;
        const maxlab::SpikeEvent * spikeEvents = fd.spikeEvents;
        file << "Struct Address: " << spikeEvents << endl;
        int spikeCount = fd.spikeCount;
        for (int j = 0; j < spikeCount; j++) {
            maxlab::SpikeEvent se = spikeEvents[j];
            file << "\tFrame: " << se.frameNo << endl;
            file << "\tChannel: " << se.channel << endl;
            
            if (!emap.exists(se.channel)) {
                file << "\tInvalid channel number" << endl;
            } else {
                tempSum++;
            }
        }
    }
    if (tempSum != sum) {
        file << "Sum discrepancy:" << endl;
        file << "\tRecorded: " << sum << endl;
        file << "\tObserved: " << tempSum << endl;
    }
    file.close();   
}

void ChannelWindow::print() {
    std::fstream file;
    file.open("ERR_LOG", std::fstream::out | std::fstream::app);
    file << "Printing window ----------------------------" << endl;
    file << "Size: " << size << endl;
    file << "Window Length: " << window.size() << endl;
    file << "Sum: " << sum << endl;
    for (int i = 0; i < size; i++) {
        maxlab::FilteredFrameData fd = get(i);
        file << "Index " << i << endl;
        file << "Spike count: " << fd.spikeCount << endl;
        const maxlab::SpikeEvent * spikeEvents = fd.spikeEvents;
        int spikeCount = fd.spikeCount;
        for (int j = 0; j < spikeCount; j++) {
            maxlab::SpikeEvent se = spikeEvents[j];
            file << "\tFrame: " << se.frameNo << endl;
        }
    }
    file.close();
}

int ChannelWindow::addEvent(maxlab::SpikeEvent se) {
    if (emap.exists(se.channel)) {
        // cout << "activity detected from channel " << se.channel << endl;
        sum++;
        return 1;
    }

    return 0;
}