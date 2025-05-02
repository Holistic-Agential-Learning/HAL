/**
 * @file channelWindow.cpp
 * @author Trevor Sullivan (trevor.sullivan@tufts.edu)
 * @brief Implementation of the ChannelWindow Class
 * @version 0.1
 * @date 2024-09-18
 * 
 * @copyright Copyright (c) 2024
 * 
 */


#include <fstream>
#include <cmath>
#include <string>
#include <vector>
#include <map>
#include <iostream>
#include <algorithm>

#include "channelWindow.h"
#include "maxlab.h"
#include "electrodeMap.h"


using namespace maxlab;
using namespace std;

ChannelWindow::ChannelWindow() {
    size = 0;
    sum = 0;
    spikeWindow = vector<maxlab::FilteredFrameData>();
    newWindowCount = 0;
    pastData = vector<struct WindowData>();
    numPastWindows = 0;
}

ChannelWindow::ChannelWindow(int length, ElectrodeMap electrodeMap, int toSave) {
    emap = electrodeMap;
    size = length;
    sum = 0;
    newWindowCount = 0;
    numPastWindows = toSave;
}

ChannelWindow::ChannelWindow(int length, const char *configPath, int toSave) {
    emap = ElectrodeMap(configPath);
    size = length;
    sum = 0;
    newWindowCount = 0;
    numPastWindows = toSave;
}

void ChannelWindow::init() {
    for (int i = 0; i < size; i++) {
        maxlab::FilteredFrameData frameData;
        maxlab::Status status = maxlab::DataStreamerFiltered_receiveNextFrame(&frameData);

        if (status == maxlab::Status::MAXLAB_NO_FRAME) {
            i--;
            continue;
        }

        addFrame(frameData);
    }
}

void ChannelWindow::addFrame(maxlab::FilteredFrameData frame) {
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
    
    spikeWindow.push_back(frame);

    if (numPastWindows) {
        newWindowCount++;
        
        // a completely new, unique window has been created
        if (newWindowCount == size) {
            pastData.push_back(getWindowData());
            newWindowCount = 0;
        }
    }
}

struct WindowData ChannelWindow::getWindowData() {
    struct WindowData winData;
    winData.firingRate = firingRate();

    return winData;
}

void ChannelWindow::shift(maxlab::FilteredFrameData frame) {
    if (spikeWindow.size() < size) {
        addFrame(frame);
    } else {
        shiftFrame(frame);
    }
}

void ChannelWindow::shiftFrame(maxlab::FilteredFrameData frame) {
    maxlab::FilteredFrameData firstFrame = spikeWindow[0];
    const maxlab::SpikeEvent *spikeEvents = firstFrame.spikeEvents;
    int spikeCount = firstFrame.spikeCount;
    
    sum -= spikeCount;
    if (spikeCount > 0) {
        free((void *)firstFrame.spikeEvents);
    }
    spikeWindow.erase(spikeWindow.begin());
    
    addFrame(frame);

    // a completely new, unique window has been created
    if (numPastWindows && pastData.size() == numPastWindows + 1 && newWindowCount == 0) {
        pastData.erase(pastData.begin());
    }
}

FilteredFrameData ChannelWindow::get(int idx) {
    if (idx >= spikeWindow.size() || idx < 0) {
        // cerr << "ChannelWindow::get(): index " << idx << "out of bounds" << endl;
        throw out_of_range("ChannelWindow::get(): index out of bounds");
    }

    return spikeWindow[idx];
}

int ChannelWindow::length() {
    return size;
}

int ChannelWindow::totalSpikeCount() {
    return sum;
}

int ChannelWindow::numChannels() {
    return emap.size();
}

ElectrodeMap ChannelWindow::electrodeMap() {
    return emap;
}

// vector<float> ChannelWindow::pastWindows() {
//     return pastData;
// }

bool ChannelWindow::pastWindowsReady() {
    return (numPastWindows && newWindowCount == 0); 
}

float ChannelWindow::avgPastWindows() {
    float sum = 0;

    for (struct WindowData d: pastData) {
        sum += d.firingRate;
    }

    return sum / pastData.size();
}

float ChannelWindow::getAvgX() {
    // used to make sure that each channel is only counted once
    int channels[1024] = {0};
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
                float x_coord = emap.getX(channel);
                avgSum += x_coord;
                channels[channel] = 1;
                count++;
            }
            
        }
    }
    float average = avgSum / count;
    
    return average;
}

float ChannelWindow::getMedX() {
    // used to make sure that each channel is only counted once
    int channels[1024] = {0};
    vector<float> x_coords;

    for (int i = 0; i < size; i++) {
        FilteredFrameData fd = get(i);
        const SpikeEvent *event = fd.spikeEvents;
        int spikeCount = fd.spikeCount;
        for (int j = 0; j < spikeCount; j++) {
            int channel = event[j].channel;
            if (channels[channel] == 0) {
                float x_coord = emap.getX(channel);
                x_coords.push_back(x_coord);
                channels[channel] = 1;
            }
        }
    }

    if (x_coords.empty()) return 0;

    sort(x_coords.begin(), x_coords.end());
    size_t n = x_coords.size();

    if (n % 2 == 0) {
        return (x_coords[n/2 - 1] + x_coords[n/2]) / 2.0;
    } else {
        return x_coords[n/2];
    }
}


float ChannelWindow::firingRate() {

    return (double) sum / (double) spikeWindow.size();
}

float ChannelWindow::firingRateSD() {
    float sumPastWindows = 0;
    for (struct WindowData data: pastData) {
        sumPastWindows += data.firingRate;
    }
    float mean = sumPastWindows / pastData.size();

    float devSum = 0;
    for (struct WindowData data: pastData) {
        float rate = data.firingRate;
        devSum += (rate - mean) * (rate - mean);
    }

    return sqrt(devSum / pastData.size());
}

void ChannelWindow::debug(string message) {
    std::fstream file;
    file.open("ERR_LOG", std::fstream::out | std::fstream::app);
    file << "Debugging window ----------------------------" << endl;
    file << message << endl;
    file << "Size: " << size << endl;
    file << "Window Length: " << spikeWindow.size() << endl;
    file << "Sum: " << sum << endl;
    int tempSum = 0;
    for (int i = 0; i < spikeWindow.size(); i++) {
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
    file << "Window Length: " << spikeWindow.size() << endl;
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
        sum++;
        return 1;
    }

    return 0;
}