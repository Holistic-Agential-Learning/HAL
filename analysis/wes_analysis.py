import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import h5py
import sys
import os
import maxlab as mx
from scipy.signal import find_peaks
from scipy.ndimage import gaussian_filter1d


sys.path.append("../HALnalysis")
import analysis_package as mla

filepath = "/run/user/1001/gvfs/smb-share:server=rstore.it.tufts.edu,share=as_rsch_levinlab_wclawson01$/Experimental Data/Summer 2024/7-9 mouse_1d_test/1/well4/"
filename = "20_min_well_4"
datapath = "data/wes_analysis/"
well_no = 4
recording_no = 0

plot = True

with h5py.File(filepath + filename + ".raw.h5", "r") as h5_file:
    h5_object = h5_file['wells']['well{0:0>3}'.format(well_no)]['rec{0:0>4}'.format(recording_no)]
    print(list(h5_object))
    #data = pd.DataFrame(np.array(h5_object["spikes"]))
    samp_rate = np.array(h5_object["settings"]["sampling"])[0]
    mapping = pd.DataFrame(np.array(h5_object["settings"]["mapping"]))

data = mla.load_spikes_from_file(filepath+ filename + ".raw.h5", well_no, recording_no)

#data["frameno"] = data["frameno"] - data.loc[0, "frameno"]
#FILTER OUT UNMAPPED CHANNELS
#may not actually be necessary: Evan's bin spike data code does this for me.
data = data.loc[data["channel"].isin(mapping["channel"]), :].reset_index(drop = True)


raster_data_filename = datapath + filename + "_spike_raster.pkl" 
spike_data_filename = datapath + filename + "_spike_data.pkl"
if os.path.isfile(raster_data_filename) and os.path.isfile(spike_data_filename):
    raster_data = pd.read_pickle(raster_data_filename)
    spike_data = pd.read_pickle(spike_data_filename)
else:
    print("Binning data...")
    raster_data, spike_data = mla.bin_spike_data(data, mapping, bin_size = 0.01)
    raster_data.to_pickle(datapath + filename + "_spike_raster.pkl")
    spike_data.to_pickle(datapath + filename + "_spike_data.pkl")


#Get total activity in each time bin, then smooth it out.
fraction_channels_active = raster_data.to_numpy().mean(axis = 1)

#Filter with gaussian convolution.
filtered_fraction_channels_active = gaussian_filter1d(fraction_channels_active, 1)



burst_thresh = 1
rms = np.sqrt(np.mean(filtered_fraction_channels_active**2))

peak_locs, properties = find_peaks(filtered_fraction_channels_active, rms * 5, distance = 30)

plt.plot(fraction_channels_active)
plt.plot(filtered_fraction_channels_active)
plt.hlines([rms * 5], 0, 240504, "r")
plt.vlines(peak_locs, 0, 1, "g")
plt.show()



num_x_bins = 43

burst_traj = np.zeros((2, len(peak_locs)))

windowsize = 50

print(mapping)

for i, loc in enumerate(peak_locs):
    xt_plot = np.zeros((2 * windowsize + 1, num_x_bins))
    avg_x_positions = np.empty(2*windowsize + 1)
    for frame in range(-windowsize, windowsize + 1):
        x_positions = list()
        if loc + frame < 0 or loc + frame >= len(filtered_fraction_channels_active):
            continue

        channels_with_spikes = list()
        for channel in raster_data.columns:
            if raster_data.loc[loc + frame, channel]:
                channels_with_spikes.append(channel)
        
        x_vals = mapping.loc[mapping["channel"].isin(channels_with_spikes), "x"]

        space_bin_counts, _ = np.histogram(x_vals, num_x_bins, (0, 3850))
        avg_x_positions[windowsize + frame] = (np.mean(x_vals))
        xt_plot[windowsize + frame, :] = space_bin_counts
    
    plt.figure()
    plt.title(f"frame = {loc}")
    plt.xlabel("space bins")
    plt.ylabel("time")

    
    plt.imshow(xt_plot, extent = [0, 3850, loc + windowsize, loc - windowsize], aspect = 'auto')
    plt.plot(avg_x_positions, np.arange(loc - windowsize, loc + windowsize + 1), "g")
    
    # old_yticks = plt.yticks()[0]
    # print(old_yticks)
    # plt.yticks(old_yticks, old_yticks + loc - windowsize)

    # plt.ylim(2*windowsize + 1, 0)
plt.show() 
plt.close()
    












# synchornized_bursts_df, burst_times_df = mla.find_synchronized_bursts(data, delta_t = 0.05, plot_firing = True)
# print(synchornized_bursts_df)
# print(burst_times_df)