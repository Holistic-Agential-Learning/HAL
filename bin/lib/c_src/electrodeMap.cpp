/**
 * @file electrodeMap.cpp
 * @author Trevor Sullivan (trevor.sullivan@tufts.edu)
 * @brief Implementation of the ElectrodeMap Class
 * @version 0.1
 * @date 2024-09-18
 * 
 * @copyright Copyright (c) 2024
 * 
 */

#include "electrodeMap.h"

#include <iostream>

using namespace std;

ElectrodeMap::ElectrodeMap() {
    
}


ElectrodeMap::ElectrodeMap(const char *config_path) {
    FILE *file = fopen(config_path, "r");
    if (file == NULL) {
        cout << "Config path is not valid: " << config_path << endl;
        exit(1);
    }
    // assert(file != NULL);

    readConfig(file);

    fclose(file);
}

bool ElectrodeMap::exists(int channelNo) {
    if (emap.count(channelNo) > 0) {
        return true;
    } 

    return false;
}

electrodeCoords ElectrodeMap::get(int channelNo) {
    if(emap.count(channelNo) > 0){
        electrodeCoords ecoords = emap[channelNo];
        return ecoords;
    }
    else{
        electrodeCoords not_found;
        not_found.position = -1;
        not_found.x = -1;
        not_found.y = -1;

        return not_found;
    }
}

int ElectrodeMap::getPosition(int channelNo) {
    if(emap.count(channelNo) > 0){
        electrodeCoords ecoords = emap[channelNo];
        return ecoords.position;
    }
    else{
        return -1;
    }
    
}

float ElectrodeMap::getX(int channelNo) {
    if(emap.count(channelNo) > 0){
        electrodeCoords ecoords = emap[channelNo];
        return ecoords.x;
    }
    else{
        return -1;
    }
}

float ElectrodeMap::getY(int channelNo) {
    if(emap.count(channelNo) == 1){
        electrodeCoords ecoords = emap[channelNo];
        return ecoords.y;
    }
    else{
        return -1;
    }
}

int ElectrodeMap::size() {
    return emap.size();
}

void ElectrodeMap::print() {
    for (map<int, electrodeCoords>::iterator it = emap.begin(); it != emap.end(); it++) {
        electrodeCoords coords = it->second;
        cout << it->first << ": " << coords.position << "(" << coords.x << ", " << coords.y << ")" << endl;
    }
}

void ElectrodeMap::readConfig(FILE *file){
    if (file == NULL) {
        cout << "NULL FILE" << endl;
    }
    string currWord;
    electrodeCoords currCoords;
    int currChannelNo;

    while (true) {
        char c = getc(file);

        if (c == '(') { // channel number
            currChannelNo = stoi(currWord);
            currWord = "";
        } else if (c == ')') { // electrode number
            currCoords.position = stoi(currWord);
            currWord = "";
        } else if (c == '/') { // x
            currCoords.x = stof(currWord);
            currWord = "";
        } else if (c == ';') { // y
            currCoords.y = stof(currWord);
            currWord = "";

            emap[currChannelNo] = currCoords;
        } else if (c == 'H') { // end of config
            break;
        } else {
            currWord += c;
        }
    }
}