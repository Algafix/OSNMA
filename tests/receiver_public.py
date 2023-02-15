#
# Copyright © European Union 2022
#
# Licensed under the EUPL, Version 1.2 or – as soon they will be approved by
# the European Commission - subsequent versions of the EUPL (the "Licence");
# You may not use this work except in compliance with the Licence.
# You may obtain a copy of the Licence at:
# https://joinup.ec.europa.eu/collection/eupl/eupl-text-eupl-12
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the Licence is distributed on an "AS IS" basis,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#
# See the Licence for the specific language governing permissions and limitations under the Licence.
#

import sys
sys.path.insert(0, '..')

from osnma.receiver.receiver import OSNMAReceiver
from osnma.receiver.input import SBFAscii
from osnma.receiver.input_sbf import SBF, SBFLive
from osnma.receiver.input_galmon import GALMON


def sbf_config1():

    config_dict = {
        'scenario_path': 'scenarios/config1/nominal_noheaders.csv',
        'exec_path': 'scenarios/config1/',
        'pubk_name': 'OSNMA_PublicKey_1.xml'
    }

    #max_iter = 600
    # ADKD12
    # max_iter = 1400
    max_iter = 40000  # 3349 Authenticated

    input_module = SBFAscii(config_dict['scenario_path'])
    osnma_r = OSNMAReceiver(input_module, config_dict)

    osnma_r.start(max_iter)


def sbf_config2():
    config_dict = {
        'scenario_path': 'scenarios/config2/conf2_nominal_noheaders.csv',
        'pubk_name': 'OSNMA_PublicKey_3.xml',
        'exec_path': 'scenarios/config2/'
    }

    # max_iter = 10000
    max_iter = 40000  # 5507 authenticated # 40 failed (CRC)

    input_module = SBFAscii(config_dict['scenario_path'])
    osnma_r = OSNMAReceiver(input_module, config_dict)

    osnma_r.start(max_iter)


def sbf_config4():
    # EXPERIMENTAL
    config_dict = {
        'scenario_path': 'scenarios/config4/conf4_nominal_noheaders.csv',
        'pubk_name': 'OSNMA_PublicKey_5.xml',
        'exec_path': 'scenarios/config4/'
    }

    # max_iter = 10000
    max_iter = 40000  # XXXX authenticated # XX failed (CRC)

    input_module = SBFAscii(config_dict['scenario_path'])
    osnma_r = OSNMAReceiver(input_module, config_dict)

    osnma_r.start(max_iter)


def sbf_config5():
    config_dict = {
        'scenario_path': 'scenarios/config5/conf5_nominal_noheaders.csv',
        'pubk_name': 'OSNMA_PublicKey_8.xml',
        'exec_path': 'scenarios/config5/'
    }
    
    # max_iter = 2500
    max_iter = 60000  # 5039 authenticated # 21 failed (CRC)

    input_module = SBFAscii(config_dict['scenario_path'])
    osnma_r = OSNMAReceiver(input_module, config_dict)

    osnma_r.start(max_iter)


def sbf_config7():

    config_dict = {
        'scenario_path': 'scenarios/config7/nominal_noheaders.csv',
        'exec_path': 'scenarios/config7/',
        'pubk_name': 'OSNMA_PublicKey_test.xml'
    }

    # max_iter = 20000
    # ADKD12
    # max_iter = 1400
    max_iter = 80000  # 3349 Authenticated

    input_module = SBFAscii(config_dict['scenario_path'])
    osnma_r = OSNMAReceiver(input_module, config_dict)

    osnma_r.start(max_iter)


def sbf_eoc_1():
    config_dict = {
        'scenario_path': 'scenarios/eoc/eoc_noheaders.csv',
        'pubk_name': 'OSNMA_PublicKey_9.xml',
        'exec_path': 'scenarios/eoc/'
    }

    max_iter = 14000  # 5945 # 4 failed (crc)
    #max_iter = 4000

    input_module = SBFAscii(config_dict['scenario_path'])
    osnma_r = OSNMAReceiver(input_module, config_dict)

    osnma_r.start(max_iter)


def sbf_npk_1():
    config_dict = {
        'scenario_path': 'scenarios/npk_1/npk_1_noheaders.csv',
        'pubk_name': 'OSNMA_PublicKey_3.xml',
        'exec_path': 'scenarios/npk_1/'
    }
    
    max_iter = 40000  # 6184 authenticated
    # max_iter = 2000

    input_module = SBFAscii(config_dict['scenario_path'])
    osnma_r = OSNMAReceiver(input_module, config_dict)

    osnma_r.start(max_iter)


def sbf_npk_2():
    config_dict = {
        'scenario_path': 'scenarios/npk_2/npk_2_noheaders.csv',
        'pubk_name': 'OSNMA_PublicKey_4.xml',
        'exec_path': 'scenarios/npk_2/'
    }

    max_iter = 40000  # 7526 Authenticated # 8 failed (CRC)

    input_module = SBFAscii(config_dict['scenario_path'])
    osnma_r = OSNMAReceiver(input_module, config_dict)

    osnma_r.start(max_iter)


def sbf_npk_12():
    config_dict = {
        'scenario_path': 'scenarios/npk_12/npk_12_noheaders.csv',
        'pubk_name': 'OSNMA_PublicKey_3.xml',
        'exec_path': 'scenarios/npk_12/'
    }
    
    max_iter = 40000  # 4861 authenticated # 6 adkd4 failed al canvi de TOW

    input_module = SBFAscii(config_dict['scenario_path'])
    osnma_r = OSNMAReceiver(input_module, config_dict)

    osnma_r.start(max_iter)


def sbf_pkrev_1():
    
    config_dict = {
        'scenario_path': 'scenarios/pkrev_1/pkrev_1_noheaders.csv',
        'pubk_name': 'OSNMA_PublicKey_4.xml',
        'exec_path': 'scenarios/pkrev_1/'
    }
    
    max_iter = 40000  # 5357 # 11 crc failed
    #max_iter = 2000

    input_module = SBFAscii(config_dict['scenario_path'])
    osnma_r = OSNMAReceiver(input_module, config_dict)

    osnma_r.start(max_iter)


def sbf_pkrev_2():
    config_dict = {
        'scenario_path': 'scenarios/pkrev_2/pkrev_2_noheaders.csv',
        'exec_path': 'scenarios/pkrev_2/'
    }

    max_iter = 40000  # 1720 # 17 crc failed

    input_module = SBFAscii(config_dict['scenario_path'])
    osnma_r = OSNMAReceiver(input_module, config_dict)

    osnma_r.start(max_iter)


def sbf_pkrev_2_with_pk():
    config_dict = {
        'scenario_path': 'scenarios/pkrev_2_with_pk/pkrev_2_noheaders.csv',
        'pubk_name': 'OSNMA_PublicKey_5.xml',
        'exec_path': 'scenarios/pkrev_2_with_pk/'
    }
    
    max_iter = 40000  # 1721 # 17 crc failed
    #max_iter = 2000

    input_module = SBFAscii(config_dict['scenario_path'])
    osnma_r = OSNMAReceiver(input_module, config_dict)

    osnma_r.start(max_iter)


def sbf_pkrev_12():
    config_dict = {
        'scenario_path': 'scenarios/pkrev_12/pkrev_12_noheaders.csv',
        'pubk_name': 'OSNMA_PublicKey_4.xml',
        'exec_path': 'scenarios/pkrev_12/'
    }
    
    max_iter = 40000  # 7115 # 28 crc failed
    #max_iter = 2000

    input_module = SBFAscii(config_dict['scenario_path'])
    osnma_r = OSNMAReceiver(input_module, config_dict)

    osnma_r.start(max_iter)


def sbf_config1_hot_start():
    config_dict = {
        'scenario_path': 'scenarios/start_scenarios/config1_hot_start/nominal_noheaders.csv',
        'pubk_name': 'OSNMA_PublicKey_1.xml',
        'exec_path': 'scenarios/start_scenarios/config1_hot_start/',
        'kroot_name': 'OSNMA_last_KROOT.txt'
    }

    max_iter = 600
    # ADKD12
    # max_iter = 1400
    #max_iter = 40000  # 3349 Authenticated

    input_module = SBFAscii(config_dict['scenario_path'])
    osnma_r = OSNMAReceiver(input_module, config_dict)

    osnma_r.start(max_iter)


def sbf_config1_wrong_pubk():
    config_dict = {
        'scenario_path': 'scenarios/start_scenarios/config1_wrong_PubK/nominal_noheaders.csv',
        'pubk_name': 'OSNMA_PublicKey_3.xml',
        'exec_path': 'scenarios/start_scenarios/config1_wrong_PubK/'
    }

    max_iter = 600
    # ADKD12
    # max_iter = 1400
    #max_iter = 40000  # 3349 Authenticated

    input_module = SBFAscii(config_dict['scenario_path'])
    osnma_r = OSNMAReceiver(input_module, config_dict)

    osnma_r.start(max_iter)


def sbf_config1_wrong_kroot():
    config_dict = {
        'scenario_path': 'scenarios/start_scenarios/config1_wrong_kroot/nominal_noheaders.csv',
        'pubk_name': 'OSNMA_PublicKey_1.xml',
        'exec_path': 'scenarios/start_scenarios/config1_wrong_kroot/',
        'kroot_name': 'OSNMA_last_KROOT.txt'
    }

    max_iter = 400
    # ADKD12
    # max_iter = 1400
    #max_iter = 40000  # 3349 Authenticated

    input_module = SBFAscii(config_dict['scenario_path'])
    osnma_r = OSNMAReceiver(input_module, config_dict)

    osnma_r.start(max_iter)


def sbf_config1_wrong_kroot_id():
    
    config_dict = {
        'scenario_path': 'scenarios/start_scenarios/config1_wrong_kroot_pkid/nominal_noheaders.csv',
        'pubk_name': 'OSNMA_PublicKey_1.xml',
        'exec_path': 'scenarios/start_scenarios/config1_wrong_kroot_pkid/',
        'kroot_name': 'OSNMA_last_KROOT.txt'
    }

    max_iter = 400
    # ADKD12
    # max_iter = 1400
    #max_iter = 40000  # 3349 Authenticated

    input_module = SBFAscii(config_dict['scenario_path'])
    osnma_r = OSNMAReceiver(input_module, config_dict)

    osnma_r.start(max_iter)


def sbf_current_config():
    config_dict = {
        'scenario_path': 'scenarios/current_config/current_config.sbf',
        'exec_path': 'scenarios/current_config/',
        'pubk_name': 'OSNMA_PublicKey.xml'
    }

    # max_iter = 600
    # ADKD12
    # max_iter = 1400
    max_iter = 40000  #

    input_module = SBF(config_dict['scenario_path'])
    osnma_r = OSNMAReceiver(input_module, config_dict)

    osnma_r.start(max_iter)


def sbf_current_config_14h():
    config_dict = {
        'scenario_path': 'scenarios/current_config_14h/current_config_14h.sbf',
        'exec_path': 'scenarios/current_config_14h/',
        'pubk_name': 'OSNMA_PublicKey.xml'
    }

    # max_iter = 600
    # ADKD12
    # max_iter = 1400
    max_iter = 400000  #

    input_module = SBF(config_dict['scenario_path'])
    osnma_r = OSNMAReceiver(input_module, config_dict)

    osnma_r.start(max_iter)


def sbf_live():
    config_dict = {
        'exec_path': 'scenarios/live/',
        'pubk_name': 'OSNMA_PublicKey.xml'
    }

    max_iter = 40000  #

    input_module = SBFLive('192.168.3.1',20000)
    osnma_r = OSNMAReceiver(input_module, config_dict)

    osnma_r.start(max_iter)


def galmon_live():
    config_dict = {
        'exec_path': 'scenarios/galmon_live/',
        'pubk_name': 'OSNMA_PublicKey.xml'
    }

    max_iter = 40000  #

    input_module = GALMON()
    osnma_r = OSNMAReceiver(input_module, config_dict)

    osnma_r.start(max_iter)


def sbf_live_parc_leopold():
    config_dict = {
        'scenario_path': 'scenarios/live_parc_leopold/parc_leopold.sbf',
        'exec_path': 'scenarios/live_parc_leopold',
        'pubk_name': 'OSNMA_PublicKey.xml'
    }

    input_module = SBF(config_dict['scenario_path'])
    osnma_r = OSNMAReceiver(input_module, config_dict)

    #osnma_r.start(1200)
    osnma_r.start()


def sbf_live_palace_to_parlament():
    config_dict = {
        'scenario_path': 'scenarios/live_palace_to_parlament/palace_to_parlament.sbf',
        'exec_path': 'scenarios/live_palace_to_parlament',
        'pubk_name': 'OSNMA_PublicKey.xml'
    }

    input_module = SBF(config_dict['scenario_path'])
    osnma_r = OSNMAReceiver(input_module, config_dict)

    #osnma_r.start(1200)
    osnma_r.start()


def sbf_live_manneken():
    config_dict = {
        'scenario_path': 'scenarios/live_to_manneken/to_manneken.sbf',
        'exec_path': 'scenarios/live_to_manneken',
        'pubk_name': 'OSNMA_PublicKey.xml'
    }

    input_module = SBF(config_dict['scenario_path'])
    osnma_r = OSNMAReceiver(input_module, config_dict)

    #osnma_r.start(1200)
    osnma_r.start()


if __name__ == "__main__":

    sbf_live_parc_leopold()
    #sbf_live_palace_to_parlament()  # 1 tag failed: (13, 0, 6) PRN_A: 13 GST_SF: 1210 52530 TAG0
    #sbf_live_manneken()
    # 3 tags failed
    # (10, 0, 5) PRN_A: 10 GST_SF: 1210 37830 TAG0
    # (36, 0, 7) PRN_A: 36 GST_SF: 1210 38880 TAG0
    # (9, 0, 2) PRN_A: 9 GST_SF: 1210 40290 TAG0

    #galmon_live()

    #sbf_live()
    #sbf_current_config()
    #sbf_current_config_14h()

    #sbf_config1()
    #sbf_config2()
    #sbf_config4()
    #sbf_config5()
    #sbf_config7()

    #sbf_eoc_1()

    #sbf_npk_1()
    #sbf_npk_2()
    #sbf_npk_12()

    #sbf_pkrev_1()
    #sbf_pkrev_2()
    #sbf_pkrev_2_with_pk()
    #sbf_pkrev_12()

    #sbf_config1_hot_start()
    #sbf_config1_wrong_pubk()
    #sbf_config1_wrong_kroot()
    #sbf_config1_wrong_kroot_id()
