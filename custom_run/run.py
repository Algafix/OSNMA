
import sys
sys.path.insert(0, '..')

from osnma.receiver.receiver import OSNMAReceiver
from osnma.receiver.input_sbf import SBF


FILE_NAME = 'current_config.sbf'


def sbf_current_config():
    config_dict = {
        'scenario_path': FILE_NAME,
        'exec_path': '.',
        'pubk_name': 'OSNMA_PublicKey.xml',
        'merkle_name': 'OSNMA_MerkleTree.xml'
    }

    input_module = SBF(config_dict['scenario_path'])
    osnma_r = OSNMAReceiver(input_module, config_dict)

    osnma_r.start()


if __name__ == "__main__":
    print(f"Running file {FILE_NAME}")
    sbf_current_config()
