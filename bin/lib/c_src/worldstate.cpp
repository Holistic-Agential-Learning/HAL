/**
 * @file worldstate.cpp
 * @author Nathan Wu (nathan.wu@yale.edu)
 * @brief Implementation of the WorldState Class
 * @version 0.1
 * @date 2024-09-18
 * 
 * @copyright Copyright (c) 2024
 * 
 */

#include "worldstate.h"

#include <cassert>

void WorldState::validate(){
    assert(world_map.length() == nodes);
    assert(0 <= location && location < nodes);
}

int WorldState::remainder(int a, int b){
    return (a%b+b)%b;
}

WorldState::WorldState(){
    location = 3;
    world_map = "10000";
    nodes = world_map.length();
    location = remainder(location, nodes);
}

WorldState::WorldState(string map, int loc){
    location = loc;
    world_map = map;
    nodes = world_map.length();
    location = remainder(location, nodes);
}

void WorldState::display(){
    validate();
    
    cout << " ";
    for(int i = 0; i < location; i++){
        cout << "  ";
    }
    cout << "@";
    cout << endl;

    for(int i = 0; i < nodes; i++){
        if(i == 0){
            cout << "┌";
        }
        else{
            cout << "─";
        }

        cout << world_map[i];
    }
    cout << "┐" << endl;

    cout << "└";
    for(int i = 0; i < 2*nodes-1; i++){
        cout << "─";
    }
    cout << "┘" << endl;
}

void WorldState::moveLeft(){
    this->location = remainder(location - 1, nodes);
    display();
}

void WorldState::moveRight(){
    this->location = remainder(location + 1, nodes);
    display();
}

char WorldState::getPosition(){
    return world_map[location];
}