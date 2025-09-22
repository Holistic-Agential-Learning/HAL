#include <iostream>

#include "hal.h"


int main(int argc, char * argv[])
{
    if (argc < 2)
    {
        std::cerr << "Call with:\t" << argv[0] << "\t[detection_channel]" << std::endl;
        exit(1);
    }
    const int detection_channel = atoi(argv[1]);

    uint8_t targetWell{0};
    uint64_t blanking{0};
    maxlab::checkVersions();
    maxlab::verifyStatus(maxlab::DataStreamerFiltered_open(maxlab::FilterType::IIR));

    // std::cout << ("stimulation_well"+std::to_string(targetWell)).c_str() << std::endl;


    maxlab::FilteredFrameData frameData;
    while (true)
    {

        maxlab::Status status = maxlab::DataStreamerFiltered_receiveNextFrame(&frameData);
        if (status == maxlab::Status::MAXLAB_NO_FRAME)
            continue;

        if (frameData.frameInfo.well_id != targetWell)
            continue;

        if (blanking > 0)
        {
            blanking--;
            if (blanking != 0)
                continue;
        }

        for (uint64_t i = 0; i < frameData.spikeCount; ++i)
        {
            const maxlab::SpikeEvent & spike = frameData.spikeEvents[i];
            if (spike.channel == detection_channel)
            {
                // const maxlab::Status status = maxlab::sendSequence(("stimulation_well"+std::to_string(targetWell)).c_str());
                const maxlab::Status status = maxlab::sendSequence("stimulation");

                blanking = 8000;
                if (status != maxlab::Status::MAXLAB_OK)
                {
                    maxlab::Response response = maxlab::sendRaw("get_errors");
                    std::cerr << "An error occured:\t" << response.content << std::endl;
                    maxlab::freeResponse(&response);
                }
            }
        }
    }
    maxlab::verifyStatus(maxlab::DataStreamerFiltered_close());
}
