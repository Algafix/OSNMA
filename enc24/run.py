import sys
sys.path.insert(0, '..')

from osnma.receiver.receiver import OSNMAReceiver
from osnma.input_formats.input_sbf import SBF

def run_osnma(config_dict, start_at):

    input_module = SBF(config_dict['scenario_path'])
    osnma_r = OSNMAReceiver(input_module, config_dict)

    osnma_r.start(start_at_gst=start_at)


prev_conf_p1 = {
    'scenario_path': 'prev_config_p1/previous_config_part1_inav.sbf',
    'exec_path': 'prev_config_p1/',
    'pubk_name': 'OSNMA_PublicKey.xml',
    'merkle_name': 'OSNMA_MerkleTree.xml',
    'kroot_name': 'OSNMA_start_KROOT.txt'
}

prev_conf_p2 = {
    'scenario_path': 'prev_config_p2/previous_config_part2_inav.sbf',
    'exec_path': 'prev_config_p2/',
    'pubk_name': 'OSNMA_PublicKey.xml',
    'merkle_name': 'OSNMA_MerkleTree.xml',
    'kroot_name': 'OSNMA_start_KROOT.txt'
}

if __name__ == "__main__":

    run_osnma(prev_conf_p1, (1266,390800))
    #run_osnma(prev_conf_p2, (1266,405655))
