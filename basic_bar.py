"""
Create a basic bar chart with the average Hg response to a pure tone of f0,
pure tones of other frequencies, stacks of f0 multiples w/o f0 present, and
the stack with 2f0, 3f0, 4f0, 5f0

One for each channel
"""
from argparse import ArgumentParser
import numpy as np
import os

import matplotlib.pyplot as plt

from pynwb import NWBHDF5IO

from utils import find_mask

def basic_bar(nwbfile, outdir, freq, identifier, ext):
    io = NWBHDF5IO(nwbfile, 'a')
    nwb = io.read()

    proc_dset = nwb.modules['Hilb_54bands'].data_interfaces['ECoG']
    rate = proc_dset.rate
    stim_dur = 0.1
    stim_dur_samp = int(stim_dur*rate)

    for ch in range(128):
        # compute average Hg response to pure tone
        f0_idxs = np.logical_and(
            nwb.trials['freq'][:] == freq,
            find_mask(nwb, [1, 0, 0, 0, 0])
        )
        f0_times = nwb.trials['start_time'][f0_idxs]
        f0_samples = (f0_times*rate).astype('int')
        f0_data = np.stack(
            proc_dset.data[i:i+stim_dur_samp, ch, 29:36] for i in f0_samples
        )
        f0_hg = np.average(f0_data, axis=-1)
        f0_hg_trial_avg = np.average(f0_hg, axis=0)
        f0_peak_hg_response = np.max(f0_hg_trial_avg)

        # compute average Hg response to other pure tones
        non_f0_idxs = np.logical_and(
            nwb.trials['freq'][:] != freq,
            find_mask(nwb, [1, 0, 0, 0, 0])
        )
        non_f0_times = nwb.trials['start_time'][non_f0_idxs]
        non_f0_samples = (non_f0_times*rate).astype('int')
        non_f0_data = np.stack(
            proc_dset.data[i:i+stim_dur_samp, ch, 29:36] for i in non_f0_samples
        )
        non_f0_hg = np.average(non_f0_data, axis=-1)
        non_f0_hg_trial_avg = np.average(non_f0_hg, axis=0)
        non_f0_peak_hg_response = np.max(non_f0_hg_trial_avg)



        # Plot them
        x = np.arange(2)
        plt.bar(x, [f0_peak_hg_response, non_f0_peak_hg_response])
        plt.xticks(x, ['f0', 'non-f0'])

        plt.savefig(os.path.join(args.outdir, 'basic_bar_{}_{}.{}'.format(freq, identifier, ext)))

        

if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('--nwbfile', '--nwb', type=str, required=True,
                        help='location of nwb file to analyze')
    parser.add_argument('--outdir', type=str, required=True,
                        help='name of directory to save plots')
    parser.add_argument('--freq', type=float, required=False, default=500.0)
    parser.add_argument('--ext', '--filetype', type=str, required=False, default='pdf',
                        help='file extension for plots (anything recognized by matplotlib)')
    parser.add_argument('--identifier', type=str, required=False, default='',
                        help='string to append to filename')

    args = parser.parse_args()

    basic_bar(args.nwbfile, args.outdir, args.freq, args.identifier, args.ext)
