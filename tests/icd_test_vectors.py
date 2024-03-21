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
import re
import logging
from pathlib import Path

from osnma.receiver.receiver import OSNMAReceiver
from osnma.input_formats.input_misc import ICDTestVectors
import osnma.utils.logger_factory as logger_factory
LOGS_PATH = Path(__file__).parent / 'logs/icd_test_logs/'


def get_base_logger_and_file_handler():
    base_logger = logger_factory.get_logger('osnma')
    file_handler = None
    log_filename = None

    for handler in base_logger.handlers:
        if isinstance(handler, logging.FileHandler):
            file_handler = handler
            log_filename = file_handler.baseFilename
            break

    return base_logger, file_handler, log_filename

def run(input_module, config_dict, expected_results_dict):

    osnma_r = OSNMAReceiver(input_module, config_dict)
    osnma_r.start()

    base_logger, file_handler, log_filename = get_base_logger_and_file_handler()
    base_logger.removeHandler(file_handler)

    with open(log_filename, 'r') as log_file:
        log_text = log_file.read()

        tags_auth = len(re.findall(r'Tag AUTHENTICATED', log_text))
        data_auth = len(re.findall(r'INFO .* AUTHENTICATED: ADKD', log_text))
        kroot_auth = len(re.findall(r'INFO .*KROOT.*\n\tAUTHENTICATED\n', log_text))
        broken_kroot = len(re.findall('WARNING.*Broken HKROOT', log_text))
        crc_failed = len(re.findall('WARNING.*CRC', log_text))
        warnings = len(re.findall('WARNING', log_text))
        errors = len(re.findall('ERROR', log_text))

    # print(f'{tags_auth} vs {expected_results_dict["tags_auth"]}')
    # print(f'{data_auth} vs {expected_results_dict["data_auth"]}')
    # print(f'{kroot_auth} vs {expected_results_dict["kroot_auth"]}')
    # print(f'{broken_kroot} vs {expected_results_dict["broken_kroot"]}')
    # print(f'{crc_failed} vs {expected_results_dict["crc_failed"]}')
    # print(f'{warnings} vs {expected_results_dict["warnings"]}')
    # print(f'{errors} vs {expected_results_dict["errors"]}')

    assert tags_auth == expected_results_dict["tags_auth"]
    assert data_auth == expected_results_dict["data_auth"]
    assert kroot_auth == expected_results_dict["kroot_auth"]
    assert broken_kroot == expected_results_dict["broken_kroot"]
    assert crc_failed == expected_results_dict["crc_failed"]
    assert warnings == expected_results_dict["warnings"]
    assert errors == expected_results_dict["errors"]

def test_vectors_icd_configuration_1(log_level=logging.INFO):
    config_dict = {
        'console_log_level': log_level,
        'logs_path': LOGS_PATH,
        'scenario_path': Path(__file__).parent / 'icd_test_vectors/configuration_1/16_AUG_2023_GST_05_00_01_fixed.csv',
        'exec_path': Path(__file__).parent / 'icd_test_vectors/configuration_1/',
        'pubk_name': 'OSNMA_PublicKey.xml'
    }

    expected_results = {
        "tags_auth": 12532,
        "data_auth": 6144,
        "kroot_auth": 176,
        "broken_kroot": 0,
        "crc_failed": 0,
        "warnings": 0,
        "errors": 0
    }

    input_module = ICDTestVectors(config_dict['scenario_path'])
    run(input_module, config_dict, expected_results)

def test_vectors_icd_configuration_2(log_level=logging.INFO):
    config_dict = {
        'console_log_level': log_level,
        'logs_path': LOGS_PATH,
        'scenario_path': Path(__file__).parent / 'icd_test_vectors/configuration_2/27_JUL_2023_GST_00_00_01_fixed.csv',
        'exec_path': Path(__file__).parent / 'icd_test_vectors/configuration_2/'
    }

    expected_results = {
        "tags_auth": 11427,
        "data_auth": 6056,
        "kroot_auth": 115,
        "broken_kroot": 17,  # The first page for all satellites has no OSNMA data
        "crc_failed": 0,
        "warnings": 17,
        "errors": 0
    }

    input_module = ICDTestVectors(config_dict['scenario_path'])
    run(input_module, config_dict, expected_results)

def test_vectors_icd_configuration_2_pubk_kroot(log_level=logging.INFO):
    config_dict = {
        'console_log_level': log_level,
        'logs_path': LOGS_PATH,
        'scenario_path': Path(__file__).parent / 'icd_test_vectors/configuration_2_pubk_kroot/27_JUL_2023_GST_00_00_01_fixed.csv',
        'exec_path': Path(__file__).parent / 'icd_test_vectors/configuration_2_pubk_kroot/',
        'pubk_name': 'OSNMA_PublicKey_2.xml',
        'kroot_name': 'OSNMA_start_KROOT.txt'
    }

    expected_results = {
        "tags_auth": 11427,
        "data_auth": 6056,
        "kroot_auth": 115,
        "broken_kroot": 17,  # The first page for all satellites has no OSNMA data
        "crc_failed": 0,
        "warnings": 17,
        "errors": 0
    }

    input_module = ICDTestVectors(config_dict['scenario_path'])
    run(input_module, config_dict, expected_results)

def test_vectors_oam_step_1(log_level=logging.INFO):
    config_dict = {
        'console_log_level': log_level,
        'logs_path': LOGS_PATH,
        'scenario_path': Path(__file__).parent / 'icd_test_vectors/oam_step1/07_OCT_2023_GST_18_45_01_fixed.csv',
        'exec_path': Path(__file__).parent / 'icd_test_vectors/oam_step1/',
        'pubk_name': 'OSNMA_PublicKey_1.xml'
    }

    expected_results = {
        "tags_auth": 6648,
        "data_auth": 3161,
        "kroot_auth": 109,
        "broken_kroot": 0,
        "crc_failed": 0,
        "warnings": 2332,
        "errors": 0
    }

    input_module = ICDTestVectors(config_dict['scenario_path'])
    run(input_module, config_dict, expected_results)

def test_vectors_oam_step_2(log_level=logging.INFO):
    config_dict = {
        'console_log_level': log_level,
        'logs_path': LOGS_PATH,
        'scenario_path': Path(__file__).parent / 'icd_test_vectors/oam_step2/07_OCT_2023_GST_19_45_01_fixed.csv',
        'exec_path': Path(__file__).parent / 'icd_test_vectors/oam_step2/',
        'pubk_name': 'OSNMA_PublicKey_1.xml'
    }

    expected_results = {
        "tags_auth": 0,
        "data_auth": 0,
        "kroot_auth": 1,
        "broken_kroot": 20,
        "crc_failed": 0,
        "warnings": 2289,
        "errors": 0
    }

    input_module = ICDTestVectors(config_dict['scenario_path'])
    run(input_module, config_dict, expected_results)

if __name__ == "__main__":

    general_log_level = logging.CRITICAL
    test_passed = 0
    test_done = 0

    print(f"\nNominal Configuration 1")
    try:
        test_vectors_icd_configuration_1(general_log_level)
    except AssertionError:
        print(f"\tFAILED")
    else:
        test_passed += 1
        print(f"\tCORRECT")
    finally:
        test_done += 1

    print(f"\nNominal Configuration 2")
    try:
        test_vectors_icd_configuration_2(general_log_level)
    except AssertionError:
        print(f"\tFAILED")
    else:
        test_passed += 1
        print(f"\tCORRECT")
    finally:
        test_done += 1

    print(f"\nNominal Configuration 2 with pubk and kroot")
    try:
        test_vectors_icd_configuration_2_pubk_kroot(general_log_level)
    except AssertionError:
        print(f"\tFAILED")
    else:
        test_passed += 1
        print(f"\tCORRECT")
    finally:
        test_done += 1

    print(f"\nOSNMA Alert Message Step 1")
    try:
        test_vectors_oam_step_1(general_log_level)
    except AssertionError:
        print(f"\tFAILED")
    else:
        test_passed += 1
        print(f"\tCORRECT")
    finally:
        test_done += 1

    print(f"\nOSNMA Alert Message Step 2")
    try:
        test_vectors_oam_step_2(general_log_level)
    except AssertionError:
        print(f"\tFAILED")
    else:
        test_passed += 1
        print(f"\tCORRECT")
    finally:
        test_done += 1

    print('\n=====================================')
    print(f'\tTEST PASSED: {test_passed}/{test_done}')
    print('=====================================')
