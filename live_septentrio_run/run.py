
import argparse
import sys
sys.path.insert(0, '..')

from osnma.receiver.receiver import OSNMAReceiver
from osnma.input_formats.input_sbf import SBFLive


parser = argparse.ArgumentParser(description='Runs OSNMAlib using GALMON live data.')
args = parser.parse_args()


def live_sbf_config():
    config_dict = {
        'exec_path': '.',
        'pubk_name': 'OSNMA_PublicKey.xml',
        'merkle_name': 'OSNMA_MerkleTree.xml'
    }

    input_module = SBFLive('192.168.3.1',20000)
    osnma_r = OSNMAReceiver(input_module, config_dict)

    osnma_r.start()


if __name__ == "__main__":

    print(f"Running using Septentrio SBF live data.")
    live_sbf_config()
