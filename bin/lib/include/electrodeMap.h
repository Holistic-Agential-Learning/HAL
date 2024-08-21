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

        /**
         * @brief Construct a new Electrode Map object
         * 
         */
        ElectrodeMap();
        
        /**
         * @brief Construct a new Electrode Map object
         * 
         * @param config_path <code>char</code> array (c string) representing 
         *                      the full path of the config file 
         */
        ElectrodeMap(const char *config_path);

        /**
         * @brief Checks if a channel number exists in the config
         * 
         * @param channelNo <code>int</code> representing the channel number of
         *                   the target electrode
         * @return <code>true</code> if the channel number exists, 
         *         <code>false</code> otherwise
         */
        bool exists(int channelNo);

        /**
         * @brief Gets the positional data of an electrode given its channel 
         *          number
         * 
         * @param channelNo <code>int</code> representing the channel number of
         *                   the target electrode
         * @return <code>struct electrodeCoords</code>; if the channelNo was 
         *          not set (i.e. it wasn't in the config file), each element of
         *          the returned struct will be set to -1.
         */
        struct electrodeCoords get(int channelNo);

        /**
         * @brief Gets the electrode number of an electrode given its channel 
         *        number
         * 
         * @param channelNo <code>int</code> representing the channel number of
         *                   the target electrode
         * @return <code>int</code>; if the channelNo was not set (i.e. it 
         *          wasn't in the config file), then -1 will be returned.
         */
        int getPosition(int channelNo);

        /**
         * @brief Gets the x coordinate (in µm) of an electrode given its 
         * channel number
         * 
         * @param channelNo <code>int</code> channel to get the x coordinate of
         * @return <code>float</code>; if the channelNo was not set (i.e. it 
         *          wasn't in the config file), then -1 will be returned.
         */
        float getX(int channelNo);

        /**
         * @brief Gets the y coordinate (in µm) of an electrode given its channel 
         * number
         * 
         * @param channelNo <code>int</code> channel to get the y coordinate of
         * @return <code>float</code>; if the channelNo was not set (i.e. it 
         *          wasn't in the config file), then -1 will be returned.
         */
        float getY(int channelNo);

        /**
         * @brief Gets the number of mapped channels in the configuration
         * 
         * @return <code>int</code>
         */
        int size();

        /**
         * @brief prints the ElectrodeMap
         * 
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
