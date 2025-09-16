'''
Takes an Activity Scan, finds active electrodes, and performs electrode selection based on user-specified algorithm. 
Outputs a list of electrodes for a Network Scan. 

Author: cgrass
'''

import numpy as np
import pandas as pd
import h5py

def load_activity_scan(filepath: str):

    data = {}

    with h5py.File(filepath, 'r') as f:
        
        # See all contents of h5 file
        # def print_h5(name, obj):
        #     print(name, type(obj))
        # f.visititems(print_h5)

        record_time_sec = int(f[f'/assay/inputs/record_time'][0]) # recording time in seconds

        for well_long in list(f[f'/wells/'].keys()):
            well = int(well_long[-1]) # well values range from 0-5
            well_data = {}
            
            for recording in list(f[f'/wells/{well_long}/']): # collect all of the recording data
                
                # print(well, recording)

                # Extract spiking data, sample rate, channel mapping, least significant bit
                
                spike_data = f[f'/wells/{well_long}/{recording}/spikes'][:] # [frame_number, channel, amplitude]
                samp_rate = f[f'/wells/{well_long}/{recording}/settings/sampling'][:][0] # value
                mapping = f[f'/wells/{well_long}/{recording}/settings/mapping'][:] # [channel, electrode, x, y]
                lsb = f[f'/wells/{well_long}/{recording}/settings/lsb'][:][0] # value

                well_data[recording] = {}
                well_data[recording]['spike_data'] = pd.DataFrame(spike_data)
                well_data[recording]['samp_rate'] = samp_rate
                well_data[recording]['mapping'] = pd.DataFrame(mapping)
                well_data[recording]['lsb'] = lsb

            data[well] = merge_recordings(well_data)
            data[well]['rec_length_sec'] = record_time_sec
    
    return data

def merge_recordings(data):
    all_data = {}
    for rec in data.values():
        for key, val in rec.items():
            all_data.setdefault(key, []).append(val)

    all_data['spike_data'] = pd.concat(all_data['spike_data'], ignore_index=True).sort_values('frameno')
    all_data['mapping'] = pd.concat(all_data['mapping'], ignore_index=True)

    for key in ['samp_rate', 'lsb']:
        if np.all(np.isclose(all_data[key], all_data[key][0])):
            all_data[key] = all_data[key][0]
        else:
            raise ValueError("Some recordings have different sampling rate or lsb.")
        
    return all_data

def get_active_channels(data: dict):
    
    for well in data:

        spike_data = data[well]['spike_data']

        # Apply applitude filter to remove spikes with amplitudes > 20 microvolts
        spike_df = pd.DataFrame(spike_data)
        # print(len(np.unique(spike_df['channel'])))
    
        amp_filtered = spike_df[spike_df['channel'] * data[well]['lsb'] * 1e6 > 20]
        # print(len(np.unique(amp_filtered['channel'])))

        # # Apply firing rate filter
        fr_amp_filtered = amp_filtered.groupby('channel').filter(lambda g: len(g)/(data[well]["rec_length_sec"]) > 0.1) # firing rate > 0.1 Hz
        # print(len(np.unique(fr_amp_filtered['channel'])))

        data[well]['active_channels'] = fr_amp_filtered

    return data

def activity_scan_results(data: dict):
    # TODO: mean firing rate, spike amplitude, and active channels plots 
    pass

def network_selection(data, dist_thresh=70, max_num_electrodes=1020, preference='random'):
    # TODO: add a minimum spike amplitude and minimum firing rate criteria for electrode selection

    for well in data:
        spike_data = data[well]['spike_data']
        channel_map = data[well]['mapping']

        selected_channels = []

        # select electrode based on preference and add to the list of selected channels
        # random selection
        curr_chan = np.random.choice(np.unique(spike_data['channel']))

        # while there are still electrodes left to select or there are no electrodes left to select that meet the conditions

            # select an electrode within the distance 

            # get electrodes dist_thresh from curr_chan 
            # filter out selected channels 
            # get current selected channels x,y location
            # curr_chan_x = 0
            # curr_chan_y = 0
            # create new column that's euclidean distance
            # filter df based on dist_thresh to get available channels 
                # if length of df is 0, decrease the threshold and repeat (while loop?)
            # select randomly from the available channels 

        pass

def select_electrodes(AS_filepath: str):
    data = load_activity_scan(AS_filepath)
    activity_scan_results(data)
    data = get_active_channels(data)
    network = network_selection(data)

if __name__ == '__main__':

    AS_path = '../../../data/AS Testing/M07474 DIV27/data.raw.h5'
    # AS_path = '../../../data/AS Testing/M09072 DIV16/data.raw.h5'

    select_electrodes(AS_path)

