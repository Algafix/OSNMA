
import argparse
import sys
sys.path.insert(0, '..')

from osnma.receiver.receiver import OSNMAReceiver
from osnma.input_formats.input_gnss_sdr import GNSS_SDR


parser = argparse.ArgumentParser(description='Runs OSNMAlib using GNSS SDR data.')
args = parser.parse_args()

def gnss_sdr_config():
    config_dict = {
        'exec_path': '.',
        'pubk_name': 'OSNMA_PublicKey_1.xml',
        'merkle_name': 'OSNMA_MerkleTree.xml',
        'kroot_name': 'OSNMA_start_KROOT.txt'
    }

    input_module = GNSS_SDR()  # Default host='127.0.0.1', port=1234, wn=None
    #input_module = GNSS_SDR(wn=1263)
    osnma_r = OSNMAReceiver(input_module, config_dict)

    osnma_r.start()


if __name__ == "__main__":
    print(f"OSNMA updated its Public Key to ID 2 on 2025-12-10 10:00 UTC. "
          f"Use Public Key 1 for data before that date.")
    print(f"Running using GNSS SDR data.")
    gnss_sdr_config()
