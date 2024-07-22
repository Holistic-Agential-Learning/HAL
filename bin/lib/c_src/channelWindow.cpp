#include "channelWindow.h"
#include <fstream>

using namespace maxlab;

ChannelWindow::ChannelWindow() {
    size = 0;
    sum = 0;
    spikeWindow = vector<maxlab::FilteredFrameData>();
    newWindowCount = 0;
    savesWindows = false;
    pastData = vector<float>();
    numPastWindows = 0;
}

ChannelWindow::ChannelWindow(int length, ElectrodeMap electrodeMap, int toSave) {
    emap = electrodeMap;
    size = length;
    sum = 0;
    newWindowCount = 0;
    savesWindows = toSave;
    numPastWindows = toSave;
}

ChannelWindow::ChannelWindow(int length, const char *configPath, int toSave) {
    emap = ElectrodeMap(configPath);
    size = length;
    sum = 0;
    newWindowCount = 0;
    savesWindows = toSave;
    numPastWindows = toSave;
}

void ChannelWindow::shiftOrAdd(maxlab::FilteredFrameData frame) {
    if (spikeWindow.size() < size) {
        addFrame(frame);
    } else {
        shiftFrame(frame);
    }
}

void ChannelWindow::add(maxlab::FilteredFrameData frame) {
    addFrame(frame);
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

    if (savesWindows) {
        newWindowCount++;
        
        // a completely new, unique window has been created
        if (newWindowCount == size) {
            pastData.push_back(stdDev());
            newWindowCount = 0;
        }
    }
}

void ChannelWindow::shift(maxlab::FilteredFrameData frame) {
    shiftFrame(frame);
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
    if (savesWindows && pastData.size() == numPastWindows + 1 && newWindowCount == 0) {
        pastData.erase(pastData.begin());
    }
}

FilteredFrameData ChannelWindow::get(int idx) {
    if (idx >= size || idx < 0) {
        exit(1);
    }

    return spikeWindow[idx];
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

vector<float> ChannelWindow::pastWindows() {
    return pastData;
}

bool ChannelWindow::pastWindowsReady() {
    return (savesWindows && newWindowCount == 0); 
}

float ChannelWindow::avgPastWindows() {
    float sum = 0;

    for (int i = 0; i < pastData.size(); i++) {
        sum += pastData[i];
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
    if (sum > 0 && avgSum == 0 && count == 0) {
        cout << "average is nan, sum is " << sum << endl;  
        debug("average is nan");
    }
    return average;
}

float ChannelWindow::stdDev() {
    // cout << "sum: " << sum << endl << spikeWindow.size() << endl;
    return (float) sum / (float) spikeWindow.size();
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