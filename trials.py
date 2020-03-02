"""
Given a preprocessed nwb file and the params text file, populate the trials table
"""

from argparse import ArgumentParser
from itertools import zip_longest
import numpy as np

from pynwb import NWBHDF5IO

# for debugging
import matplotlib.pyplot as plt

def grouper(n, iterable, padvalue=None):
    "grouper(3, 'abcdefg', 'x') --> ('a','b','c'), ('d','e','f'), ('g','x','x')"
    return zip_longest(*[iter(iterable)]*n, fillvalue=padvalue)

MASKS = [
    [1, 1, 1, 1, 1],
    [1, 1, 1, 1, 0],
    [1, 1, 1, 0, 0],
    [1, 1, 0, 0, 0],
    [0, 0, 0, 1, 1],
    [0, 0, 1, 1, 1],
    [0, 1, 1, 1, 1],
    [0, 0, 1, 1, 0],
    [0, 1, 1, 0, 0],

    # Pure tones
    [1, 0, 0, 0, 0],
    [0, 1, 0, 0, 0],
    [0, 0, 1, 0, 0],
    [0, 0, 0, 1, 0],
    [0, 0, 0, 0, 1],
]

def iter_all_symbols(params_file):
    """
    iterate over all symbols, defined by tab separation, skipping those with no digits
    """
    with open(params_file, 'r') as infile:
        data = infile.read()
        for xstr in data.split('\t'):
            digits = ''.join(x for x in xstr if x.isdigit())
            if digits:
                yield digits
            else:
                continue

def iter_mask_freq(params_file):
    with open(params_file, 'r') as infile:
        data = infile.read()
        for idxstr, freqstr in grouper(2, iter_all_symbols(params_file), None):
            idx = int(idxstr)
            freq = float(freqstr)
            yield MASKS[idx], freq

def get_stim_onsets(nwb):
    # nwb = open nwbfile
    THRESH = 0.2
    stim = nwb.stimulus['recorded_stim'].data[:]
    thresh_crossings = np.diff( (stim > THRESH).astype('int'), axis=0)
    stim_onsets = np.where(thresh_crossings > 0.5)[0] + 1

    # Clean them up. Some extra onsets are detected in the middle of the sound,
    # probably due to sampling artifacts, so if the distance between any two
    # onsets is less than 6100 samples, remove one
    diff_stim_onsets = np.diff(stim_onsets)
    while np.any(diff_stim_onsets < 6100):
        first_wrong = np.argmax(diff_stim_onsets < 6100) + 1
        stim_onsets = np.delete(stim_onsets, first_wrong)
        diff_stim_onsets = np.diff(stim_onsets)
    
    return stim_onsets

def populate_trials_table(nwbfile, params_file):
    io = NWBHDF5IO(nwbfile, 'a')
    nwb = io.read()
    rate = nwb.stimulus['recorded_stim'].rate
    stim_dur = 0.1 # seconds
    stim_onsets = get_stim_onsets(nwb)
    mask_freqs = list(iter_mask_freq(params_file))

    nwb.add_trial_column(name='mask', description='which multiples of the fundamental were presented')
    nwb.add_trial_column(name='freq', description='fundamental frequency of stack presented')
    nwb.add_trial_column(name='freqs', description='comma-concatenated strings of frequencies presented')
    for stim_onset, (mask, freq) in zip(stim_onsets, mask_freqs):
        start_time = stim_onset/rate
        freqs = ','.join(str((i+1)*freq) for i, present in enumerate(mask) if present)
        nwb.add_trial(start_time=start_time, stop_time=start_time+stim_dur, mask=mask, freq=freq, freqs=freqs)

    io.write(nwb)
    io.close()

if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('--nwbfile', '--nwb', type=str, required=True)
    parser.add_argument('--params-file', type=str, required=False, default='params96k_16int.txt')

    args = parser.parse_args()

    populate_trials_table(args.nwbfile, args.params_file)
