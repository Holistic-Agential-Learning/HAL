/**
 * @file worldstate.h
 * @author Nathan Wu (nathan.wu@yale.edu)
 * @brief Header file for the WorldState Class
 * @version 0.1
 * @date 2024-09-18
 * 
 * @copyright Copyright (c) 2024
 * 
 */

#ifndef __WORLDSTATE_H__
#define __WORLDSTATE_H__

#include <iostream>

using namespace std;


class WorldState {
    public:
        int location;
        string world_map;//How do we encode different types of rewards? Maybe a char * of length "nodes"?

        WorldState();

        /**
         * @brief Construct a new World State object
         * 
         * @param map <code>string</code> representing the layout of the world
         * @param loc <code>int</code> indicating the starting position
         */
        WorldState(string map, int loc);

        /**
         * @brief Prints the world state
         * 
         */
        void display();

        /**
         * @brief Moves left by one
         * 
         */
        void moveLeft();

        /**
         * @brief Moves right by one
         * 
         */
        void moveRight();

        /**
         * @brief Get the current position
         * 
         * @return <code>char</code>
         */
        char getPosition();

    private:
        int nodes;
        
        //int resetTime;
        //int currentTime;
        //bool circular;
        
        void validate();

        int remainder(int a, int b);
};

#endif
