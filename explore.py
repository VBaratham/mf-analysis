"""
Just read the nwbfile into the variable `nwb` and start a debugger
"""
from argparse import ArgumentParser
from pynwb import NWBHDF5IO

if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('--nwbfile', '--nwb', type=str, required=True)

    args = parser.parse_args()

    io = NWBHDF5IO(args.nwbfile, 'r')
    nwb = io.read()
    import ipdb; ipdb.set_trace()
