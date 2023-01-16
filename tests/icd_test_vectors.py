import sys
sys.path.insert(0, '..')

from osnma.receiver.receiver import OSNMAReceiver
from osnma.receiver.input import ICDTestVectors


def icd_test_vectors_configuration_A():

    config_dict = {
        'scenario_path': 'icd_test_vectors/configuration_A/13_DEC_2020_GST_09_00_01_fixed.csv',
        'exec_path': 'icd_test_vectors/configuration_A/',
        'pubk_name': 'OSNMA_PublicKey_2.xml'
    }

    #max_iter = 2000
    max_iter = 0

    input_module = ICDTestVectors(config_dict['scenario_path'])
    osnma_r = OSNMAReceiver(input_module, config_dict)

    osnma_r.start(max_iter)


if __name__ == "__main__":

    icd_test_vectors_configuration_A()
