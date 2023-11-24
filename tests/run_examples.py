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
from pathlib import Path

from osnma.receiver.receiver import OSNMAReceiver
from osnma.input_formats.input_sbf import SBF, SBFLive
from osnma.input_formats.input_misc import ICDTestVectors
from osnma.input_formats.input_galmon import GALMON

LOGS_PATH = Path(__file__).parent / 'logs/general_logs/'


def sbf_live():
    config_dict = {
        'exec_path': 'scenarios/live/',
        'pubk_name': 'OSNMA_PublicKey.xml'
    }

    input_module = SBFLive('192.168.3.1', 20000)
    osnma_r = OSNMAReceiver(input_module, config_dict)

    osnma_r.start()


def galmon_live():
    config_dict = {
        'exec_path': 'scenarios/galmon_live/',
        'pubk_name': 'OSNMA_PublicKey.xml'
    }

    input_module = GALMON()
    osnma_r = OSNMAReceiver(input_module, config_dict)

    osnma_r.start()


def sbf_new_config():
    config_dict = {
        'scenario_path': 'scenarios/new_live_config/osnma_new_config.sbf',
        'exec_path': 'scenarios/new_live_config/',
        'pubk_name': 'OSNMA_PublicKey.xml'
    }

    input_module = SBF(config_dict['scenario_path'])
    osnma_r = OSNMAReceiver(input_module, config_dict)

    osnma_r.start()

def test_vectors_icd_configuration_1():
    config_dict = {
        'logs_path': LOGS_PATH,
        'scenario_path': Path(__file__).parent / 'icd_test_vectors/configuration_1/16_AUG_2023_GST_05_00_01_fixed.csv',
        'exec_path': Path(__file__).parent / 'icd_test_vectors/configuration_1/',
        'pubk_name': 'OSNMA_PublicKey.xml'
    }

    input_module = ICDTestVectors(config_dict['scenario_path'])
    osnma_r = OSNMAReceiver(input_module, config_dict)
    osnma_r.start()

def test_vectors_icd_configuration_2():
    config_dict = {
        'logs_path': LOGS_PATH,
        'scenario_path': Path(__file__).parent / 'icd_test_vectors/configuration_2/27_JUL_2023_GST_00_00_01_fixed.csv',
        'exec_path': Path(__file__).parent / 'icd_test_vectors/configuration_2/'
    }

    input_module = ICDTestVectors(config_dict['scenario_path'])
    osnma_r = OSNMAReceiver(input_module, config_dict)
    osnma_r.start()

def test_vectors_icd_configuration_2_pubk_kroot():
    config_dict = {
        'logs_path': LOGS_PATH,
        'scenario_path': Path(__file__).parent / 'icd_test_vectors/configuration_2_pubk_kroot/27_JUL_2023_GST_00_00_01_fixed.csv',
        'exec_path': Path(__file__).parent / 'icd_test_vectors/configuration_2_pubk_kroot/',
        'pubk_name': 'OSNMA_PublicKey_2.xml',
        'kroot_name': 'OSNMA_start_KROOT.txt'
    }

    input_module = ICDTestVectors(config_dict['scenario_path'])
    osnma_r = OSNMAReceiver(input_module, config_dict)
    osnma_r.start()

def test_change_of_word_type_5():

    config_dict = {
        'logs_path': LOGS_PATH,
        'scenario_path': Path(__file__).parent / 'test_corner_cases/change_of_word_type_5/change_wt5.sbf',
        'exec_path': Path(__file__).parent / 'test_corner_cases/change_of_word_type_5/',
        'pubk_name': 'OSNMA_PublicKey.xml',
        'kroot_name': 'OSNMA_last_KROOT.txt'
    }

    input_module = SBF(config_dict['scenario_path'])
    osnma_r = OSNMAReceiver(input_module, config_dict)
    osnma_r.start()


def tow_rollover():

    config_dict = {
        'logs_path': LOGS_PATH,
        'scenario_path': Path(__file__).parent / 'test_corner_cases/tow_rollover/tow_rollover_only_inav.sbf',
        'exec_path': Path(__file__).parent / 'test_corner_cases/tow_rollover/',
        'pubk_name': 'OSNMA_PublicKey.xml'
    }

    input_module = SBF(config_dict['scenario_path'])
    osnma_r = OSNMAReceiver(input_module, config_dict)
    osnma_r.start()


if __name__ == "__main__":

    test_vectors_icd_configuration_1()

    # test_vectors_icd_configuration_2()

    # test_vectors_icd_configuration_2_pubk_kroot()

    # tow_rollover()

    # test_change_of_word_type_5()

    # sbf_new_config()

    # galmon_live()

    # sbf_live()
