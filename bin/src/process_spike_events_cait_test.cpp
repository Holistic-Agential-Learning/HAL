#include <stdlib.h>
#include <stdio.h>
#include "maxlab/maxlab.h"

int main(int argc, char * argv[]){

    if (argc<2){ // get the detection channel from command line input
        fprintf(stderr, "call with:%s [detection_channel]", argv[0]);
        exit(1)
    }

    const int detection_channel = atoi(argv[1]);

    maxlab::checkVersion();
    maxlab::verifyStatus(maxlab::DataStreamerFiltered_open(maxlab::FilterType::IIR));

    uint8_t targetWell{0};
    uint64_t blanking{0};

    maxlab::FilteredFrameData frameData;

    while (true){

        maxlab::Status status = maxlab::DataStreamerFiltered_receiveNextFrame(&frameData); //get next frame

        if (status == maxlab::Status::MAXLAB_NO_FRAME)
            continue;

        // Continue if blanking
        if (blanking > 0){
            blanking--;
            if (blanking!=0)
                continue;
        }

        // Only look at data from target well
        if (frameData.frameInfo.well_id != targetWell)
            continue;

        // iterate through spikes in frame
        for (uint64_t i=0; i<frameData.spikeCount; ++i){
            const maxlab::SpikeEvent & spike frameData.spikeEvents[i];
            if (spike.channel == detection_channel){ // if spike is detected on the specified channel, send stimulation
                const maxlab::Status status = maxlab::sendSequence("stimulation_sequence");

                blanking = 8000; //in frames

                if (status != maxlab::Status::MAXLAB_OK){
                    maxlab::Response response = maxlab::sendRaw("get_errors")
                    std::cerr << "An error occured:\t" << response.content << std::endl;
                    maxlab::freeResponse(&response);
                }
            }

        }

    }

    maxlab::verifyStatus(maxlab::DataStreamerFiltered_close());

}