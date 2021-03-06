"""
Create a tonotopy by plotting the frequency that elicits the max response on each electrode
(pure tones only)
"""

from argparse import ArgumentParser
import numpy as np
import os

import matplotlib.pyplot as plt

from pynwb import NWBHDF5IO

from utils import find_mask

def basic_tonotopy(nwbfile, outdir, identifier, ext):
    io = NWBHDF5IO(nwbfile, 'a')
    nwb = io.read()

    proc_dset = nwb.modules['Hilb_54bands'].data_interfaces['ECoG']
    rate = proc_dset.rate
    stim_dur = 0.1
    stim_dur_samp = int(stim_dur*rate)

    # Trials where pure tones were presented
    pure_tone_idxs = np.logical_or.reduce((
        find_mask(nwb, [1, 0, 0, 0, 0]),
        find_mask(nwb, [0, 1, 0, 0, 0]),
        find_mask(nwb, [0, 0, 1, 0, 0]),
        find_mask(nwb, [0, 0, 0, 1, 0]),
        find_mask(nwb, [0, 0, 0, 0, 1]),
    ))

    # Start times of all trials where pure tones were presented
    pure_tone_times = nwb.trials['start_time'][pure_tone_idxs]

    # Start time, in samples, of all trials where pure tones were presented
    start_idxs = (pure_tone_times*rate).astype('int')

    # Frequency presented in each pure tone trial
    freqs = np.array(nwb.trials['freqs'][pure_tone_idxs]).astype('float')

    def get_best_freq(ch):
        bf, bf_peak_hg = -1, 0
        for freq in np.unique(freqs):
            this_freq_trial_idxs = (freqs == freq)
            this_freq_start_idxs = start_idxs[this_freq_trial_idxs]
            this_freq_data = np.stack(
                proc_dset.data[i:i+stim_dur_samp, ch, 29:36] for i in this_freq_start_idxs
            )
            this_freq_hg = np.average(this_freq_data, axis=-1)
            this_freq_hg_trial_avg = np.average(this_freq_hg, axis=0)
            this_freq_peak_hg_response = np.max(this_freq_hg_trial_avg)
            if this_freq_peak_hg_response > bf_peak_hg:
                bf, bf_peak_hg = freq, this_freq_peak_hg_response

        return bf

    # Frequency that elicits the biggest response on each electrode, in channel order
    best_freq_ch_order = np.array([get_best_freq(ch) for ch in range(128)])

    # coordinates of ECoG electrodes
    x = nwb.electrodes['x'][:128]
    y = nwb.electrodes['y'][:128]
    
    grid_order = np.array(sorted(range(128), key=lambda i: (x[i], y[i])))

    best_freq_grid_layout = np.reshape(best_freq_ch_order[grid_order], (8, 16))

    plt.imshow(best_freq_grid_layout)
    plt.colorbar()

    plt.savefig(os.path.join(args.outdir, 'basic_tonotopy_{}.{}'.format(identifier, ext)))


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('--nwbfile', '--nwb', type=str, required=True,
                        help='location of nwb file to analyze')
    parser.add_argument('--outdir', type=str, required=True,
                        help='name of directory to save plots') 
    parser.add_argument('--ext', '--filetype', type=str, required=False, default='pdf',
                        help='file extension for plots (anything recognized by matplotlib)')
    parser.add_argument('--identifier', type=str, required=False, default='',
                        help='string to append to filename')

    args = parser.parse_args()

    basic_tonotopy(args.nwbfile, args.outdir, args.identifier, args.ext)
