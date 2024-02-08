import argparse
import sys
sys.path.insert(0, '..')

from osnma.receiver.receiver import OSNMAReceiver
from osnma.input_formats.input_ubx import UBXLiveSerial


def ubx_current_config():
    config_dict = {
        'exec_path': '.',
        'pubk_name': 'OSNMA_PublicKey_1.xml',
        'merkle_name': 'OSNMA_MerkleTree.xml'
    }

    input_module = UBXLiveSerial("COM4")
    osnma_r = OSNMAReceiver(input_module, config_dict)

    osnma_r.start()


if __name__ == "__main__":

    print(f"Running using ublox UBX live data.")
    ubx_current_config()
