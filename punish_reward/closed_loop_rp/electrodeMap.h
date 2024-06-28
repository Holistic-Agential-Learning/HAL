#ifndef __ELECTRODEMAP_H__
#define __ELECTRODEMAP_H__
#include <string>

#include <stdlib.h>
#include <map>

using namespace std;

// struct to hold positional data of electrodes
typedef struct electrodeCoords  {
    int position; // electrode number
    float x; // x coordinate (in µm)
    float y; // y coordinate (in µm)
} electrodeCoords;

class ElectrodeMap {
    public:

        ElectrodeMap();

        /* Constructor
         * 
         * Takes in path of config file (created by MaxLab software) and parses 
         * the config
         * 
         * Notes: Throws an error if file opening failed
         */
        ElectrodeMap(const char *config_path);

        /* exists
         *
         * Checks if a channel number exists in the config
         * 
         * Parameters:
         *      - channelNo: integer representing the channel to check
         * 
         * Returns: bool indicating whether a channel is in the config
         */
        bool exists(int channelNo);

        /* get
         * 
         * Gets the positional data of an electrode given its channel number
         * 
         * Parameters:
         *      - int channelNo: integer representing the channel number of the 
         *                       target electrode
         * 
         * Returns: struct electrodeCoords representing the positional data of 
         *          an electrode
         * 
         * Notes: If the channelNo was not set before the program starts (i.e. 
         *        it wasn't in the config file), then each element of the 
         *        returned struct will be set to -1.
         */
        struct electrodeCoords get(int channelNo);

        /* get_position
         * 
         * Gets the electrode number of an electrode given its channel number
         * 
         * Parameters:
         *      - int channelNo: integer representing the channel number of the 
         *                       target electrode
         * 
         * Returns: integer representing the electrode number of an electrode
         * 
         * Notes: If the channelNo was not set before the program starts (i.e. 
         *        it wasn't in the config file), then -1 will be returned.
         */
        int get_position(int channelNo);

        /* get_x
         * 
         * Gets the x coordinate (in µm) of an electrode given its channel 
         * number
         * 
         * Parameters:
         *      - int channelNo: integer representing the channel number of the 
         *                       target electrode
         * 
         * Returns: integer representing the x coordinate of an electrode
         * 
         * Notes: If the channelNo was not set before the program starts (i.e. 
         *        it wasn't in the config file), then -1 will be returned.
         */
        float get_x(int channelNo);

        /* get_y
         * 
         * Gets the y coordinate (in µm) of an electrode given its channel 
         * number
         * 
         * Parameters:
         *      - int channelNo: integer representing the channel number of the 
         *                       target electrode
         * 
         * Returns: integer representing the y coordinate of an electrode
         * 
         * Notes: If the channelNo was not set before the program starts (i.e. 
         *        it wasn't in the config file), then -1 will be returned.
         */
        float get_y(int channelNo);

        /* size
         *
         *Gets the number of channels in the configuration
         * 
         * Returns: integer representing the number of channels mapped in the configuration
         */
        int size();


        /* print
         * 
         * prints electrode map
         */
        void print();
    
    private:

        /* readConfig
         * 
         * Reads info from a given config file and populates emap
         * 
         * Parameters:
         *      FILE *file: pointer to FILE representing a valid electrode 
         *                  config file
         * 
         * Side Effects: updates emap
         */
        void readConfig(FILE *file);
        

        map<int, struct electrodeCoords> emap;

};

#endif