'''
Takes an Activity Scan, finds active electrodes, and performs electrode selection based on user-specified algorithm. 
Outputs a list of electrodes for a Network Scan. 

Author: cgrass
'''

import numpy as np
import pandas as pd
import h5py
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap, ListedColormap
from mpl_toolkits.axes_grid1 import make_axes_locatable


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
                chan_elec_df = well_data[recording]['mapping'].iloc[:, :2].copy()
                well_data[recording]['spike_data'] = well_data[recording]['spike_data'].merge(chan_elec_df, on="channel").sort_values('frameno')

            data[well] = merge_recordings(well_data)
            data[well]['rec_length_sec'] = record_time_sec

            # electrodes are unique, channels are not
            # print(len(data[well]['mapping']))
            # print(len(np.unique(data[well]['mapping']['electrode'])))
            # print(len(np.unique(data[well]['mapping']['channel'])))

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

        # Apply applitude filter to remove electrodes with amplitude 90th percentile < 20 microvolts
        # print(len(np.unique(spike_data['electrode'])))

        spike_data = spike_data[spike_data['amplitude']<0].copy() # remove any positive spikes
        amp_filtered = spike_data.groupby('electrode').filter(lambda g: np.abs(np.percentile(g["amplitude"], 90)* data[well]['lsb'] * 1e6)>20) 
        # print(len(np.unique(amp_filtered['electrode'])))

        # # Apply firing rate filter
        fr_amp_filtered = amp_filtered.groupby('electrode').filter(lambda g: len(g)/(data[well]["rec_length_sec"]) > 0.1) # firing rate > 0.1 Hz
        # print(len(np.unique(fr_amp_filtered['electrode'])))

        data[well]['active_electrodes'] = fr_amp_filtered.copy()

    return data

def activity_scan_results(data: dict, savepath: str, savefilename: str = None):
    # mean firing rate, spike amplitude, and active channels plots 

    for well in data:

        spike_data = data[well]['spike_data']
        active_electrodes = data[well]['active_electrodes']
        channel_map = data[well]['mapping']
        recording_length = data[well]['rec_length_sec']
        samp_rate = data[well]['samp_rate']
        lsb = data[well]['lsb']

        elec_size = 17.5
        chip_width = 220
        chip_height = 120
        # print(np.min(channel_map['x'])/elec_size, np.max(channel_map['x'])/elec_size)
        # print(np.min(channel_map['y'])/elec_size, np.max(channel_map['y'])/elec_size)

        # Firing rate
        fr_df = spike_data.groupby("electrode").size().reset_index(name="firing rate")
        fr_df["firing rate"] = fr_df["firing rate"] / recording_length

        # firing rate stats
        # print(np.mean(fr_df["firing rate"]))
        # print(np.std(fr_df["firing rate"]))
        # print(np.median(fr_df["firing rate"]))
        # print(np.percentile(fr_df["firing rate"], 10))
        # print(np.percentile(fr_df["firing rate"], 90))

        # ISI 
        ISI = []
        for group_name, group_df in spike_data.groupby("electrode"):
            
            ISI_msec = np.diff(group_df['frameno'])/samp_rate*1000
            ISI_filtered = ISI_msec[ISI_msec<200] # exclude ISIs greater than 200 in the mean ISI calculation 
            
            if len(ISI_filtered)>0:
                ISI.append(np.mean(ISI_filtered))
        
        # Amplitude
        amp_df = spike_data.groupby("electrode").apply(lambda g: np.abs(np.percentile(g["amplitude"], 90) * lsb * 1e6)).reset_index(name="amplitude_90")

        # Active electrodes
        total_elecs = len(np.unique(list(spike_data["electrode"])))
        active_elecs = len(np.unique(active_electrodes["electrode"]))
        percent_active = active_elecs / (total_elecs) * 100

        # Create figure

        fig = plt.figure(figsize=(14, 15))
        gs = fig.add_gridspec(3, 2, width_ratios=[2, 1], wspace=0.3)
        # fig = plt.figure(figsize=(10, 12))
        # gs = fig.add_gridspec(3, 2, width_ratios=[20, 1], height_ratios=[1,1,1], hspace=0.3, wspace=0.3)

        # Custom colormap
        # Number of colors for each segment
        n_blues = 128
        n_orrd = 128

        # Black segment
        black = np.array([[0, 0, 0, 1]])

        # Reversed Blues
        blues = plt.cm.Blues_r(np.linspace(0, 1, n_blues))

        # OrRd
        orrd = plt.cm.OrRd(np.linspace(0, 0.7, n_orrd))

        # Stack them together
        colors = np.vstack((black, blues, orrd))

        # Create colormap
        custom_cmap = LinearSegmentedColormap.from_list("black_blues_orrd_lighter", colors)

        # Firing rate
        fr_array_ax = fig.add_subplot(gs[0, 0]) 
        df = channel_map.merge(fr_df, on="electrode")

        grid = np.zeros((chip_height, chip_width))
        df['y_elec'] = (df['y']/elec_size).astype(int)
        df['x_elec'] = (df['x']/elec_size).astype(int)
        grid[df['y_elec'], df['x_elec']] = df['firing rate']

        fr_im = fr_array_ax.matshow(grid, cmap=custom_cmap, vmin=0, vmax=5, aspect='equal', interpolation='none')
        fr_array_ax.set_axis_off()
        fr_array_ax.margins(0)
        fr_array_ax.set_title('Firing Rate')
        plt.colorbar(fr_im, ax=fr_array_ax, label='Firing Rate [Hz]', shrink=0.8)

        fr_hist_ax = fig.add_subplot(gs[0, 1]) 
        fr_min, fr_max = 0,6
        fr_hist_ax.hist(fr_df[(fr_df["firing rate"]>fr_min) & (fr_df["firing rate"]<fr_max)]["firing rate"], bins=50, color='dodgerblue')
        fr_hist_ax.set_xlabel('Firing Rate [Hz]')
        fr_hist_ax.set_ylabel('Electrode Count')
        fr_hist_ax.spines['top'].set_visible(False)
        fr_hist_ax.spines['right'].set_visible(False)

        # Amplitude
        amp_array_ax = fig.add_subplot(gs[1, 0]) 
        df = channel_map.merge(amp_df, on="electrode")

        grid = np.zeros((chip_height, chip_width))
        df['y_elec'] = (df['y']/elec_size).astype(int)
        df['x_elec'] = (df['x']/elec_size).astype(int)
        grid[df['y_elec'], df['x_elec']] = df['amplitude_90']

        amp_im = amp_array_ax.matshow(grid, cmap=custom_cmap)
        amp_array_ax.set_axis_off()
        amp_array_ax.set_aspect("equal")
        amp_array_ax.margins(0)
        amp_array_ax.set_title('Spike Amplitude')
        plt.colorbar(amp_im, ax=amp_array_ax, label='Amplitude [µV]', shrink=0.8)

        amp_hist_ax = fig.add_subplot(gs[1, 1]) 
        amp_hist_ax.hist(amp_df["amplitude_90"], bins=50, color='dodgerblue')
        amp_hist_ax.set_xlabel('Spike Amplitude [µV]')
        amp_hist_ax.set_ylabel('Electrode Count')
        amp_hist_ax.spines['top'].set_visible(False)
        amp_hist_ax.spines['right'].set_visible(False)

        # Active electrodes
        active_elec_array_ax = fig.add_subplot(gs[2, 0])  
        df = channel_map[channel_map["electrode"].isin(list(active_electrodes["electrode"]))].copy()

        grid = np.zeros((chip_height, chip_width))
        df['y_elec'] = (df['y']/elec_size).astype(int)
        df['x_elec'] = (df['x']/elec_size).astype(int)
        grid[df['y_elec'], df['x_elec']] = 1

        # Custom colormap: 0 = black, 1 = blue
        binary_cmap = ListedColormap(["black", "dodgerblue"])
        
        active_im = active_elec_array_ax.matshow(grid, cmap=binary_cmap)
        active_elec_array_ax.set_axis_off()
        active_elec_array_ax.set_aspect("equal")
        active_elec_array_ax.margins(0)
        active_elec_array_ax.set_title(f'Active Electrodes = {percent_active:.2f}%')
        plt.colorbar(active_im, ax=active_elec_array_ax, label='Active State', shrink=0.8)

        # ISI
        isi_hist_ax = fig.add_subplot(gs[2, 1]) 
        isi_hist_ax.hist(ISI, bins=50, color='dodgerblue')
        isi_hist_ax.set_xlabel('Interspike Interval [ms]')
        isi_hist_ax.set_ylabel('Electrode Count')
        isi_hist_ax.spines['top'].set_visible(False)
        isi_hist_ax.spines['right'].set_visible(False)

        if savefilename:
            plt.savefig(savepath+f'/{savefilename}_well{well}.png', bbox_inches='tight', dpi=300)
        else:
            plt.savefig(savepath+f'/well{well}_AS_results_cgrass.png', bbox_inches='tight', dpi=300)
        plt.close()


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

        # while there are still electrodes left to select or the distance threshold is too small
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
                
                if dist_thresh < 17: # stop looking, distance threshold is less than one electrode
                    stop = True
                    break
                
                dist_thresh -= 17

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

def network_scan_results(data, savepath:str, savefilename: str = None):

    for well in data:

        network = data[well]['recording_electrodes']
        channel_map = data[well]['mapping']
        chip_height = 120
        chip_width = 220
        elec_size = 17.5
    
        # Selected electrodes

        fig, ax = plt.subplots(1)

        df = channel_map[channel_map["electrode"].isin(network)].copy()

        grid = np.zeros((chip_height, chip_width))
        df['y_elec'] = (df['y']/elec_size).astype(int)
        df['x_elec'] = (df['x']/elec_size).astype(int)
        grid[df['y_elec'], df['x_elec']] = 1

        # Custom colormap: 0 = black, 1 = blue
        binary_cmap = ListedColormap(["black", "red"])
        
        active_im = ax.matshow(grid, cmap=binary_cmap, aspect='equal')
        plt.axis('off')
        plt.title('Network')
        # --- make colorbar match height ---

        divider = make_axes_locatable(ax)
        cax = divider.append_axes("right", size="5%", pad=0.05)  # size = width of cbar
        cbar = fig.colorbar(active_im, cax=cax)
        cbar.set_label("Selected")

        if savefilename:
            plt.savefig(savepath+f'/{savefilename}_well{well}.png', bbox_inches='tight', dpi=300)
        else:
            plt.savefig(savepath+f'/well{well}_network.png', bbox_inches='tight', dpi=300)
        plt.close()

def save_network(data: dict, savepath: str, savefilename: str = None):
    
    for well in data:
        
        if savefilename:
            np.savez(savepath+f'/{savefilename}_well{well}.npz', recording_electrodes=data[well]['recording_electrodes'])
        else:    
            np.savez(savepath+f'/well{well}_network.npz', recording_electrodes=data[well]['recording_electrodes'])
    

def select_electrodes(AS_filepath: str, save_path:str=None):

    # TODO: pass in a 'wells' parameter which lets you select from the h5 file which wells you'd like to process in case you don't want to do all of them.


    # Activity scan
    data = load_activity_scan(AS_filepath)
    data = get_active_electrodes(data)
    activity_scan_results(data, savepath=AS_filepath.split('/data.raw.h5')[0])

    # Network scan
    data = network_selection(data)
    network_scan_results(data, savepath=save_path)
    save_network(data, savepath=save_path)

    rec_elecs = {}
    for well in data:
        rec_elecs[well] = data[well]['recording_electrodes'] # returns dictionary of recording electrodes with wellno as key 
    
    return rec_elecs

if __name__ == '__main__':

    AS_path = '../../../data/AS Testing/M07474 DIV27/data.raw.h5'
    # AS_path = '../../../data/AS Testing/M07474 DIV33/data.raw.h5'
    # AS_path = '../../../data/AS Testing/M09072 DIV16/data.raw.h5'

    np.random.seed(100)

    select_electrodes(AS_path)

