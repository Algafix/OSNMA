
import argparse
import sys
sys.path.insert(0, '..')

from osnma.receiver.receiver import OSNMAReceiver
from osnma.input_formats.input_sbf import SBF


parser = argparse.ArgumentParser(description='Runs OSNMAlib against the provided SBF file that contains the block '
                                             'GALRawINAV.')
parser.add_argument('sbf_file', metavar='file', type=str, default='current_config.sbf', nargs='?',
                    help='name of the SBF file.')
args = parser.parse_args()


def sbf_current_config():
    """
    config_dict contains the default value for the most interesting configuration parameters for a normal user.
    The osnma receiver can also be forced to start at a given GST (WN, TOW) by modifying the start() call. The WN needs
    to be given in the Galileo form (GPS_WN - 1024).
    """
    config_dict = {
        'scenario_path': args.sbf_file,
        'exec_path': '.',
        'merkle_name': 'OSNMA_MerkleTree.xml',
        # Always needs to be specified. Can be downloaded from the GSC website
        'pubk_name': 'OSNMA_PublicKey_1.xml',
        # Specify for Warm Start mode. Can be downloaded from the GSC website or extracted from a Cold Start run
        'kroot_name': '',
        # Specify for Hot Start mode. You may run your file with OSNMAlib and then point to the saved kroot text file
        'TL': 30,
        # Synchronization time with respect to the GST the receiver is capable of guarantee at all time
        'do_mack_partial_extraction': True,
        # Extract all information possible from a partially received mack message in a sub-frame
        'do_tesla_key_regen': True,
        # Regenerate TESLA keys from partially received keys in a sub-frame
        'do_cop_link_optimization': False,
        # To fully benefit from the COP link optimization, the TL value should be lower than 30s, best with 17s
        'do_reed_solomon_recovery': True,
        # Exploit word types 17-20 to recover word types 1-4, which are used for the ADKD0 authentication
        'do_dual_frequency': False,
        # Will only be useful if the input module sends I/NAV pages from the Galileo E5b-I signal
        'stop_at_faf': True,
        # Stops at First Authenticated Fix, returns the TTFAF, start GST, and last GST
    }

    input_module = SBF(config_dict['scenario_path'])
    osnma_r = OSNMAReceiver(input_module, config_dict)

    osnma_r.start()
    # osnma_r.start(start_at_gst=(1273,218011))


if __name__ == "__main__":

    print(f"Running file {args.sbf_file}")
    sbf_current_config()
