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


def icd_test_vectors_configuration_B():

    config_dict = {
        'scenario_path': 'icd_test_vectors/configuration_B/17_JAN_2021_GST_08_00_01_fixed.csv',
        'exec_path': 'icd_test_vectors/configuration_B/',
        'pubk_name': 'OSNMA_PublicKey_3.xml'
    }

    #max_iter = 2000
    max_iter = 0

    input_module = ICDTestVectors(config_dict['scenario_path'])
    osnma_r = OSNMAReceiver(input_module, config_dict)

    osnma_r.start(max_iter)


def icd_test_vectors_configuration_C():

    config_dict = {
        'scenario_path': 'icd_test_vectors/configuration_C/28_FEB_2021_GST_08_00_01_fixed.csv',
        'exec_path': 'icd_test_vectors/configuration_C/',
        'pubk_name': 'OSNMA_PublicKey_8.xml'
    }

    #max_iter = 2000
    max_iter = 0

    input_module = ICDTestVectors(config_dict['scenario_path'])
    osnma_r = OSNMAReceiver(input_module, config_dict)

    osnma_r.start(max_iter)


def icd_test_vectors_configuration_D():

    config_dict = {
        'scenario_path': 'icd_test_vectors/configuration_D/20_FEB_2022_GST_08_00_01_fixed.csv',
        'exec_path': 'icd_test_vectors/configuration_D/',
        'pubk_name': 'OSNMA_PublicKey_2.xml'
    }

    #max_iter = 2000
    max_iter = 0

    input_module = ICDTestVectors(config_dict['scenario_path'])
    osnma_r = OSNMAReceiver(input_module, config_dict)

    osnma_r.start(max_iter)


def icd_test_vectors_EOC_step_1():

    config_dict = {
        'scenario_path': 'icd_test_vectors/EOC_step_1/12_JAN_2021_GST_10_00_01_fixed.csv',
        'exec_path': 'icd_test_vectors/EOC_step_1/',
        'pubk_name': 'OSNMA_PublicKey_3.xml'
    }

    #max_iter = 2000
    max_iter = 0

    input_module = ICDTestVectors(config_dict['scenario_path'])
    osnma_r = OSNMAReceiver(input_module, config_dict)

    osnma_r.start(max_iter)


def icd_test_vectors_EOC_step_2():

    config_dict = {
        'scenario_path': 'icd_test_vectors/EOC_step_2/13_JAN_2021_GST_10_00_01_fixed.csv',
        'exec_path': 'icd_test_vectors/EOC_step_2/',
        'pubk_name': 'OSNMA_PublicKey_3.xml'
    }

    #max_iter = 2000
    max_iter = 0

    input_module = ICDTestVectors(config_dict['scenario_path'])
    osnma_r = OSNMAReceiver(input_module, config_dict)

    osnma_r.start(max_iter)


def icd_test_vectors_NPK_step_1():

    config_dict = {
        'scenario_path': 'icd_test_vectors/NPK_step_1/25_JAN_2021_GST_08_00_01_fixed.csv',
        'exec_path': 'icd_test_vectors/NPK_step_1/',
        'pubk_name': 'OSNMA_PublicKey_3.xml'
    }

    #max_iter = 2000
    max_iter = 0

    input_module = ICDTestVectors(config_dict['scenario_path'])
    osnma_r = OSNMAReceiver(input_module, config_dict)

    osnma_r.start(max_iter)


def icd_test_vectors_NPK_step_2():

    config_dict = {
        'scenario_path': 'icd_test_vectors/NPK_step_2/11_DEC_2020_GST_08_00_01_fixed.csv',
        'exec_path': 'icd_test_vectors/NPK_step_2/',
        'pubk_name': 'OSNMA_PublicKey_1.xml'
    }

    #max_iter = 2000
    max_iter = 0

    input_module = ICDTestVectors(config_dict['scenario_path'])
    osnma_r = OSNMAReceiver(input_module, config_dict)

    osnma_r.start(max_iter)


def icd_test_vectors_NPK_step_3():

    config_dict = {
        'scenario_path': 'icd_test_vectors/NPK_step_3/12_DEC_2020_GST_08_00_01_fixed.csv',
        'exec_path': 'icd_test_vectors/NPK_step_3/',
        'pubk_name': 'OSNMA_PublicKey_2.xml'
    }

    #max_iter = 2000
    max_iter = 0

    input_module = ICDTestVectors(config_dict['scenario_path'])
    osnma_r = OSNMAReceiver(input_module, config_dict)

    osnma_r.start(max_iter)


def icd_test_vectors_PKREV_step_1():
    config_dict = {
        'scenario_path': 'icd_test_vectors/PKREV_step_1/15_DEC_2020_GST_08_00_01_fixed.csv',
        'exec_path': 'icd_test_vectors/PKREV_step_1/',
        'pubk_name': 'OSNMA_PublicKey_2.xml'
    }

    # max_iter = 2000
    max_iter = 0

    input_module = ICDTestVectors(config_dict['scenario_path'])
    osnma_r = OSNMAReceiver(input_module, config_dict)

    osnma_r.start(max_iter)


def icd_test_vectors_PKREV_step_2():
    config_dict = {
        'scenario_path': 'icd_test_vectors/PKREV_step_2/15_DEC_2020_GST_10_00_01_fixed.csv',
        'exec_path': 'icd_test_vectors/PKREV_step_2/',
        'pubk_name': 'OSNMA_PublicKey_3.xml'
    }

    # max_iter = 2000
    max_iter = 0

    input_module = ICDTestVectors(config_dict['scenario_path'])
    osnma_r = OSNMAReceiver(input_module, config_dict)

    osnma_r.start(max_iter)


def icd_test_vectors_PKREV_step_3():
    config_dict = {
        'scenario_path': 'icd_test_vectors/PKREV_step_3/16_DEC_2020_GST_08_00_01_fixed.csv',
        'exec_path': 'icd_test_vectors/PKREV_step_3/',
        'pubk_name': 'OSNMA_PublicKey_3.xml'
    }

    # max_iter = 2000
    max_iter = 0

    input_module = ICDTestVectors(config_dict['scenario_path'])
    osnma_r = OSNMAReceiver(input_module, config_dict)

    osnma_r.start(max_iter)


def icd_test_vectors_OAM():
    config_dict = {
        'scenario_path': 'icd_test_vectors/OAM/23_FEB_2021_GST_09_00_31_fixed.csv',
        'exec_path': 'icd_test_vectors/OAM/'
    }

    # max_iter = 2000
    max_iter = 0

    input_module = ICDTestVectors(config_dict['scenario_path'])
    osnma_r = OSNMAReceiver(input_module, config_dict)

    osnma_r.start(max_iter)


if __name__ == "__main__":

    #icd_test_vectors_configuration_A()
    #icd_test_vectors_configuration_B()
    #icd_test_vectors_configuration_C()
    #icd_test_vectors_configuration_D()

    #icd_test_vectors_EOC_step_1()
    #icd_test_vectors_EOC_step_2()

    #icd_test_vectors_NPK_step_1()
    #icd_test_vectors_NPK_step_2()
    # 5 tags with ADKD 4 failed. Multiple epochs and from multiple sats, strange.
    #icd_test_vectors_NPK_step_3()

    #icd_test_vectors_PKREV_step_1()
    #icd_test_vectors_PKREV_step_2()
    # 3 tags with ADKD 4 failed. Multiple epochs and from multiple sats, strange.
    #icd_test_vectors_PKREV_step_3()

    icd_test_vectors_OAM()
