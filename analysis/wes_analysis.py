import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import h5py
import sys
import os
import maxlab as mx
from scipy.signal import find_peaks
from scipy.ndimage import gaussian_filter1d
from typing import List

sys.path.append(os.path.dirname(os.path.realpath(__file__)) + "/../../HALnalysis")
import analysis_package as mla

#Should I save the raw spike data too? From that time window?
class Burst:
    def __init__(self, time: float, num_x_bins: int, window_size: int,  num_channels: int, bin_duration: float, avg_x_positions: np.array, fraction_channels_firing: np.array, xtplot: np.array):
        self.time = time
        self.num_x_bins = num_x_bins
        self.window_size = window_size #NOTE: THE FULL SIZE OF THE WINDOW IS 2 * window_size + 1 (one window before and one window after)
        self.avg_x_positions = avg_x_positions
        self.num_channels = num_channels
        self.bin_duration = bin_duration #in seconds
        self.fraction_channels_firing = fraction_channels_firing
        self.xtplot = xtplot

    def plot(self, plot_avg_x_positions = True):
        fig = plt.figure()
        ax_dict = fig.subplot_mosaic('''
                                     aaaab
                                     '''
                                     , sharey = True)

        plt.sca(ax_dict["a"])
        plt.title(f"time = {self.time:.2f}")
        plt.xlabel("space (μm)")
        plt.ylabel("time (s)")

        plt.imshow(self.xtplot, extent = [0, 3850, self.time + (self.window_size) * self.bin_duration, self.time - (self.window_size) * self.bin_duration], aspect = 'auto')
        
        plt.plot(self.avg_x_positions, np.arange(self.time - self.window_size * self.bin_duration, self.time + (self.window_size + 0.5) * self.bin_duration, self.bin_duration), "g")


        plt.sca(ax_dict['b'])

        plt.plot(self.fraction_channels_firing, np.arange(self.time - self.window_size * self.bin_duration, self.time + (self.window_size + 0.5) * self.bin_duration, self.bin_duration), "g")
        plt.xlim([0, 1])
        plt.xlabel("Fraction of\nchannels firng")
        plt.tight_layout()
        plt.show() 



def find_bursts(filepath, filename, well_no = 0, recording_no = 0, bin_duration = 0.01, num_x_bins = 43, window_size = 50, plot = True, burst_thresh = 1, datapath = "data/wes_analysis/"):
    with h5py.File(filepath + filename + ".raw.h5", "r") as h5_file:
        h5_object = h5_file['wells']['well{0:0>3}'.format(well_no)]['rec{0:0>4}'.format(recording_no)]
        print(list(h5_object))
        #data = pd.DataFrame(np.array(h5_object["spikes"]))
        samp_rate = np.array(h5_object["settings"]["sampling"])[0]
        mapping = pd.DataFrame(np.array(h5_object["settings"]["mapping"]))

    data = mla.load_spikes_from_file(filepath+ filename + ".raw.h5", well_no, recording_no)

    print(data)

    #data["frameno"] = data["frameno"] - data.loc[0, "frameno"]
    #FILTER OUT UNMAPPED CHANNELS
    #may not actually be necessary: Evan's bin spike data code does this for me.
    data = data.loc[data["channel"].isin(mapping["channel"]), :].reset_index(drop = True)


    raster_data_filename = datapath + filename + "_spike_raster.pkl" 
    spike_data_filename = datapath + filename + "_spike_data.pkl"
    times_filename = datapath + filename + "_times.npy"
    try: 
        raster_data = pd.read_pickle(raster_data_filename)
        spike_data = pd.read_pickle(spike_data_filename)
        times = np.load(times_filename)
    except FileNotFoundError:
        print ("files not found")
        print("Binning data...")
        raster_data, spike_data, times = mla.bin_spike_data(data, mapping, bin_size = bin_duration)
        raster_data.to_pickle(raster_data_filename)
        spike_data.to_pickle(spike_data_filename)
        np.save(times_filename, times)


    #Get total activity in each time bin, then smooth it out.
    fraction_channels_active = raster_data.to_numpy().mean(axis = 1)

    #Filter with gaussian convolution.
    filtered_fraction_channels_active = gaussian_filter1d(fraction_channels_active, 1)


    rms = np.sqrt(np.mean(filtered_fraction_channels_active**2))

    peak_locs, properties = find_peaks(filtered_fraction_channels_active, rms * burst_thresh, distance = 30)

    if plot:
        plt.plot(times, fraction_channels_active)
        plt.plot(times, filtered_fraction_channels_active)
        plt.hlines([rms * 5], 0, max(times), "r")
        plt.vlines(times[peak_locs], 0, 1, "g", alpha = 0.3)
        plt.show()



    burst_list = list()
    for i, loc in enumerate(peak_locs):
        print(f"burst found in bin {loc} (time {bin_duration * loc:.2f} s)")
        xt_plot = np.zeros((2 * window_size + 1, num_x_bins))
        avg_x_positions = np.empty(2*window_size + 1)
        for frame in range(-window_size, window_size + 1):
            x_positions = list()
            if loc + frame < 0 or loc + frame >= len(filtered_fraction_channels_active):
                continue

            channels_with_spikes = list()
            for channel in raster_data.columns:
                if raster_data.loc[loc + frame, channel]:
                    channels_with_spikes.append(channel)
            
            x_vals = mapping.loc[mapping["channel"].isin(channels_with_spikes), "x"]

            space_bin_counts, _ = np.histogram(x_vals, num_x_bins, (0, 3850))
            avg_x_positions[window_size + frame] = np.mean(x_vals)
            xt_plot[window_size + frame, :] = space_bin_counts
        
        burst_list.append(Burst(times[loc], num_x_bins, window_size, np.shape(raster_data)[1], bin_duration, avg_x_positions, fraction_channels_active[loc - window_size:loc + window_size + 1], xt_plot))
    
    print("DONE")


    return burst_list






if __name__ == '__main__':
    print("hello world")



    filepath = "/run/user/1001/gvfs/smb-share:server=rstore.it.tufts.edu,share=as_rsch_levinlab_wclawson01$/Experimental Data/Summer 2024/mouse_1d/7-9 mouse_1d_test/1/well4/"
    filename = "20_min_well_4"
    datapath = "data/wes_analysis/"
    well_no = 4
    recording_no = 0


    burst_dict = find_bursts(filepath, filename, well_no, recording_no, burst_thresh = 5)

    print(burst_dict)
    print(burst_dict.keys())
    for i in range(0, len(burst_dict)):
        burst_dict[list(burst_dict.keys())[int(i)]].plot()
