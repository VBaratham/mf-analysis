import numpy as np

def find_mask(nwb, mask):
    """
    Return bool array with true for trials where the mask was the given one
    """
    mask = np.array(mask)
    masks = nwb.trials['mask'][:]
    ntrials = masks.shape[0]
    mask = np.tile(mask, (ntrials, 1))
    return np.all(masks == mask, axis=1)

