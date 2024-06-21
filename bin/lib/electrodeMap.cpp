#include <electrodeMap.h>
#include <iostream>
#include <stdio.h>
#include <cstdlib>
#include <utils.h>

using namespace std;


ElectrodeMap::ElectrodeMap(const char *config_path) {
    cout << "about to read config" << endl;
    FILE *file = fopen(config_path, "r");
    cout << "about to read config" << endl;
    if (file == NULL) {
        exit(1);
    }
    // assert(file != NULL);

    cout << "about to read config" << endl;
    readConfig(file);
    cout << "finished reading config" << endl;

    fclose(file);
}

electrodeCoords ElectrodeMap::get(int channelNo) {
    if(emap.count(channelNo) == 1){
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

int ElectrodeMap::get_position(int channelNo) {
    if(emap.count(channelNo) == 1){
        electrodeCoords ecoords = emap[channelNo];
        return ecoords.position;
    }
    else{
        return -1;
    }
    
}

float ElectrodeMap::get_x(int channelNo) {
    if(emap.count(channelNo) == 1){
        electrodeCoords ecoords = emap[channelNo];
        return ecoords.x;
    }
    else{
        return -1;
    }
}

float ElectrodeMap::get_y(int channelNo) {
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