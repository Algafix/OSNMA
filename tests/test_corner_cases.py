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
from osnma.input_formats.input_sbf import SBF
import osnma.utils.logger_factory as logger_factory
LOGS_PATH = Path(__file__).parent / 'logs/corner_cases_logs/'


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

def test_change_of_word_type_5(log_level=logging.INFO):

    config_dict = {
        'console_log_level': log_level,
        'logs_path': LOGS_PATH,
        'scenario_path': Path(__file__).parent / 'test_corner_cases/change_of_word_type_5/change_wt5.sbf',
        'exec_path': Path(__file__).parent / 'test_corner_cases/change_of_word_type_5/',
        'pubk_name': 'OSNMA_PublicKey.xml',
        'kroot_name': 'OSNMA_last_KROOT.txt'
    }

    expected_results = {
        "tags_auth": 1503,
        "data_auth": 986,
        "kroot_auth": 26,
        "broken_kroot": 6,
        "crc_failed": 0,
        "warnings": 6,
        "errors": 0
    }

    input_module = SBF(config_dict['scenario_path'])
    run(input_module, config_dict, expected_results)

def test_tow_rollover(log_level=logging.INFO):

    config_dict = {
        'console_log_level': log_level,
        'logs_path': LOGS_PATH,
        'scenario_path': Path(__file__).parent / 'test_corner_cases/tow_rollover/tow_rollover_only_inav.sbf',
        'exec_path': Path(__file__).parent / 'test_corner_cases/tow_rollover/',
        'pubk_name': 'OSNMA_PublicKey.xml'
    }

    expected_results = {
        "tags_auth": 8975,
        "data_auth": 7409,
        "kroot_auth": 199,
        "broken_kroot": 43,
        "crc_failed": 2498,
        "warnings": 2541,
        "errors": 0
    }

    input_module = SBF(config_dict['scenario_path'])
    run(input_module, config_dict, expected_results)

def test_osnma_outage_and_wt5(log_level=logging.INFO):

    config_dict = {
        'console_log_level': log_level,
        'logs_path': LOGS_PATH,
        'scenario_path': Path(__file__).parent / 'test_corner_cases/osnma_outage/osnma_outage.sbf',
        'exec_path': Path(__file__).parent / 'test_corner_cases/osnma_outage/',
        'pubk_name': 'OSNMA_PublicKey.xml',
        'kroot_name': 'OSNMA_start_KROOT.txt'
    }

    expected_results = {
        "tags_auth": 5920,
        "data_auth": 3412,
        "kroot_auth": 50,
        "broken_kroot": 25,
        "crc_failed": 49,
        "warnings": 74,
        "errors": 0
    }

    input_module = SBF(config_dict['scenario_path'])
    run(input_module, config_dict, expected_results)

def test_osnma_after_outage(log_level=logging.INFO):

    config_dict = {
        'console_log_level': log_level,
        'logs_path': LOGS_PATH,
        'scenario_path': Path(__file__).parent / 'test_corner_cases/osnma_after_outage/after_outage.sbf',
        'exec_path': Path(__file__).parent / 'test_corner_cases/osnma_after_outage/',
        'pubk_name': 'OSNMA_PublicKey.xml',
        'kroot_name': 'OSNMA_start_KROOT.txt'
    }

    expected_results = {
        "tags_auth": 4109,
        "data_auth": 2641,
        "kroot_auth": 65,
        "broken_kroot": 18,
        "crc_failed": 57,
        "warnings": 75,
        "errors": 0
    }

    input_module = SBF(config_dict['scenario_path'])
    run(input_module, config_dict, expected_results)

def test_6_hours(log_level=logging.INFO):

    config_dict = {
        'console_log_level': log_level,
        'logs_path': LOGS_PATH,
        'scenario_path': Path(__file__).parent / 'test_corner_cases/6_hours/6_hours.sbf',
        'exec_path': Path(__file__).parent / 'test_corner_cases/6_hours/',
        'pubk_name': 'OSNMA_PublicKey_1.xml'
    }

    expected_results = {
        "tags_auth": 14600,
        "data_auth": 10982,
        "kroot_auth": 198,
        "broken_kroot": 61,
        "crc_failed": 2619,
        "warnings": 2680,
        "errors": 0
    }

    input_module = SBF(config_dict['scenario_path'])
    run(input_module, config_dict, expected_results)


if __name__ == "__main__":

    general_log_level = logging.CRITICAL
    test_passed = 0
    test_done = 0

    print(f"\nChange of Word Type 5")
    try:
        test_change_of_word_type_5(general_log_level)
    except AssertionError:
        print(f"\tFAILED")
    else:
        test_passed += 1
        print(f"\tCORRECT")
    finally:
        test_done += 1

    print(f"\nToW rollover")
    try:
        test_tow_rollover(general_log_level)
    except AssertionError:
        print(f"\tFAILED")
    else:
        test_passed += 1
        print(f"\tCORRECT")
    finally:
        test_done += 1

    print(f"\nOSNMA outage")
    try:
        test_osnma_outage_and_wt5(general_log_level)
    except AssertionError:
        print(f"\tFAILED")
    else:
        test_passed += 1
        print(f"\tCORRECT")
    finally:
        test_done += 1

    print(f"\nOSNMA after outage")
    try:
        test_osnma_after_outage(general_log_level)
    except AssertionError:
        print(f"\tFAILED")
    else:
        test_passed += 1
        print(f"\tCORRECT")
    finally:
        test_done += 1

    print(f"\n6 hours")
    try:
        test_6_hours(general_log_level)
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



