'''
Takes an Activity Scan, finds active electrodes, and performs electrode selection based on user-specified algorithm. 
Outputs a list of electrodes for a Network Scan. 

Author: cgrass
'''

import numpy as np
import pandas as pd
import h5py
import matplotlib.pyplot as plt

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

                # add electrode to the spike data as a unique identifier (channels are repeated over recordings)
                chan_elec_slice = well_data[recording]['mapping'].iloc[:, :2]
                chan_elec_mapping = chan_elec_slice.set_index('channel')['electrode']
                well_data[recording]['spike_data']['electrode'] = well_data[recording]['spike_data']['channel'].map(chan_elec_mapping).astype("Int64")

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

def get_active_electrodes(data: dict):
    
    for well in data:

        spike_data = data[well]['spike_data']

        # Apply applitude filter to remove spikes with amplitudes > 20 microvolts
        spike_df = pd.DataFrame(spike_data)
        # print(len(np.unique(spike_df['electrode'])))
    
        amp_filtered = spike_df[spike_df['electrode'] * data[well]['lsb'] * 1e6 > 20]
        # print(len(np.unique(amp_filtered['electrode'])))

        # # Apply firing rate filter
        fr_amp_filtered = amp_filtered.groupby('electrode').filter(lambda g: len(g)/(data[well]["rec_length_sec"]) > 0.1) # firing rate > 0.1 Hz
        # print(len(np.unique(fr_amp_filtered['electrode'])))

        data[well]['active_electrodes'] = fr_amp_filtered.copy()

    return data

def activity_scan_results(data: dict):
    # TODO: mean firing rate, spike amplitude, and active channels plots 

    for well in data:

        spike_data = data[well]['spike_data']
        active_electrodes = data[well]['active_electrodes']
        channel_map = data[well]['mapping']
        recording_length = data[well]['rec_length_sec']
        samp_rate = data[well]['samp_rate']
        lsb = data[well]['lsb']

        # Firing rate
        fr_df = active_electrodes.groupby("electrode").size().reset_index(name="firing rate")
        fr_df["firing rate"] = fr_df["firing rate"] / recording_length

        # ISI 
        # TODO: check this... something's weird
        ISI = list(active_electrodes.groupby("electrode")['frameno'].apply(lambda x: np.mean(np.diff(x))/samp_rate*1000 if len(x) > 1 else np.nan))
        
        # Mean amplitude
        amp_df = active_electrodes.groupby("electrode")["amplitude"].mean().reset_index(name="mean amplitude")
        amp_df["mean amplitude"] = np.abs(amp_df["mean amplitude"] * lsb * 1e6) # convert to microvolts

        # Create figure

        fig = plt.figure(figsize=(8, 10))
        gs = fig.add_gridspec(3, 2)

        # TODO: check this... i think it's upside down again
        # fr_array_ax = fig.add_subplot(gs[0, 0]) 
        # df = channel_map.merge(fr_df, on="electrode")
        # chip_width = 220 # in electrodes
        # chip_height = 120 # in electrodes
        # elec_size = 17.5 # in µm

        # x_edges = np.linspace(0, chip_width*elec_size, chip_width)
        # y_edges = np.linspace(0, chip_height*elec_size, chip_height)
        # x_idx = np.digitize(df["x"], x_edges) - 1  # subtract 1 to get 0-based index
        # y_idx = np.digitize(df["y"], y_edges) - 1

        # grid = np.full((chip_height, chip_width), 0)
        # for xi, yi, val in zip(x_idx, y_idx, df["firing rate"]):
        #     grid[yi, xi] = val  # note: row = y, col = x

        # fr_im = fr_array_ax.matshow(grid, origin='lower', extent=[df["x"].min(), df["x"].max(), df["y"].min(), df["y"].max()], cmap='coolwarm', aspect='auto', vmin=0, vmax=5)
        # plt.colorbar(fr_im, label='Firing Rate [Hz]')
        # plt.xlabel("x (µm)")
        # plt.ylabel("y (µm)")

        fr_hist_ax = fig.add_subplot(gs[0, 1]) 
        fr_hist_ax.hist(fr_df["firing rate"], bins=50, color='dodgerblue')

        amp_hist_ax = fig.add_subplot(gs[1, 1]) 
        amp_hist_ax.hist(amp_df["mean amplitude"], bins=50, color='dodgerblue')

        # isi_hist_ax = fig.add_subplot(gs[2, 1]) 
        # isi_hist_ax.hist(ISI, bins=50, color='dodgerblue')

        plt.show()

        exit()

    pass

def network_selection(data, dist_thresh=100, max_num_electrodes=1020, preference='random'):
    # TODO: add a minimum spike amplitude and minimum firing rate criteria for electrode selection
    
    # max_num_electrodes = 10 #testing
    # dist_thresh = 5000 #testing

    for well in data:

        print('Selecting electrodes for well', well)

        spike_data = data[well]['active_electrodes'] # use spike data only for active electrodes
        channel_map_unfiltered = data[well]['mapping']

        # filter out inactive electrodes
        channel_map = channel_map_unfiltered[channel_map_unfiltered['electrode'].isin(list(spike_data['electrode']))]

        selected_electrodes = []

        # select electrode based on preference and add to the list of selected channels
        # random selection
        curr_elec = np.random.choice(np.unique(channel_map['electrode']))

        # while there are still electrodes left to select or there are no electrodes left to select that meet the conditions
        stop = False
        while len(selected_electrodes) < max_num_electrodes and not stop:

            # print("Current electrode:", curr_elec)

            # select an electrode outside the distance threshold 
 
            # filter out selected electrodes but keep the current electrode for distance calculations
            filtered_df = channel_map[~channel_map['electrode'].isin(selected_electrodes)].copy()
            selected_electrodes.append(curr_elec)

            # get current selected electrode's x,y location
            curr_elec_row = filtered_df[filtered_df['electrode']==curr_elec]

            # calculate all electrodes' euclidean distances from curr_elec
            filtered_df['distance'] = np.sqrt((filtered_df['x']-curr_elec_row['x'].iloc[0])**2 + (filtered_df['y']-curr_elec_row['y'].iloc[0])**2)

            # filter df based on dist_thresh to get available electrodes            
            potential_elecs = filtered_df[filtered_df['distance']>dist_thresh]

            while len(potential_elecs)==0:

                # print('Decreasing distance threhsold.')
                
                if dist_thresh < 18: # stop looking, distance threshold is less than one electrode
                    stop = True
                    break
                
                dist_thresh -= 20

                potential_elecs = filtered_df[filtered_df['distance']>dist_thresh]

                print('New distance threshold:', dist_thresh)
            
            if not stop:
                
                # select next electrode
                curr_elec = np.random.choice(list(potential_elecs['electrode']))

                # print('Next electrode:', curr_elec, ', Distance:', potential_elecs[potential_elecs['electrode']==curr_elec]['distance'].iloc[0])
 
        # print('Selected electrodes:', selected_electrodes)
        print('Num. selected electrodes:', len(selected_electrodes))
        print()

        data[well]['recording_electrodes'] = selected_electrodes

    return data

def network_scan_results(data):
    pass
    

def select_electrodes(AS_filepath: str):

    # Activity scan
    data = load_activity_scan(AS_filepath)
    data = get_active_electrodes(data)
    activity_scan_results(data)

    exit()

    # Network scan
    data = network_selection(data)
    network_scan_results(data)

if __name__ == '__main__':

    AS_path = '../../../data/AS Testing/M07474 DIV27/data.raw.h5'
    # AS_path = '../../../data/AS Testing/M09072 DIV16/data.raw.h5'

    np.random.seed(100)

    select_electrodes(AS_path)

