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
from osnma.input_formats.input_sbf import SBF, SBFAscii
import osnma.utils.logger_factory as logger_factory
LOGS_PATH = Path(__file__).parent / 'test_logs/'


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


def test_sbf_config1(log_level=logging.INFO):
    config_dict = {
        'console_log_level': log_level,
        'logs_path': LOGS_PATH,
        'scenario_path': Path(__file__).parent / 'scenarios/config1/config1.sbf',
        'exec_path': Path(__file__).parent / 'scenarios/config1/',
        'pubk_name': 'OSNMA_PublicKey_1.xml'
    }

    input_module = SBF(config_dict['scenario_path'])
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
        warnings = len(re.findall('WARNING', log_text))
        errors = len(re.findall('ERROR', log_text))

    assert tags_auth == 1625
    assert data_auth == 1033
    assert kroot_auth == 25
    assert broken_kroot == 3
    assert warnings == 4
    assert errors == 0


def test_sbf_config2(log_level=logging.INFO):
    config_dict = {
        'console_log_level': log_level,
        'logs_path': LOGS_PATH,
        'scenario_path': Path(__file__).parent / 'scenarios/config2/config2.sbf',
        'pubk_name': 'OSNMA_PublicKey_3.xml',
        'exec_path': Path(__file__).parent / 'scenarios/config2/'
    }

    input_module = SBF(config_dict['scenario_path'])
    osnma_r = OSNMAReceiver(input_module, config_dict)
    osnma_r.start()

    base_logger, file_handler, log_filename = get_base_logger_and_file_handler()
    base_logger.removeHandler(file_handler)

    with open(log_filename, 'r') as log_file:
        log_text = log_file.read()

        tags_auth = len(re.findall(r'Tag AUTHENTICATED', log_text))
        data_auth = len(re.findall(r'INFO .* AUTHENTICATED: ADKD', log_text))
        kroot_auth = len(re.findall(r'INFO .*KROOT.*\n\tAUTHENTICATED\n', log_text))
        warnings = len(re.findall('WARNING', log_text))
        crc_failed = len(re.findall('WARNING.*CRC', log_text))
        broken_kroot = len(re.findall('WARNING.*Broken HKROOT', log_text))
        errors = len(re.findall('ERROR', log_text))

    assert tags_auth == 3416
    assert data_auth == 1254
    assert kroot_auth == 23
    assert crc_failed == 39
    assert broken_kroot == 3
    assert warnings == 43
    assert errors == 0


def test_sbf_config5(log_level=logging.INFO):
    config_dict = {
        'console_log_level': log_level,
        'logs_path': LOGS_PATH,
        'scenario_path': Path(__file__).parent / 'scenarios/config5/config5.sbf',
        'pubk_name': 'OSNMA_PublicKey_8.xml',
        'exec_path': Path(__file__).parent / 'scenarios/config5/'
    }

    input_module = SBF(config_dict['scenario_path'])
    osnma_r = OSNMAReceiver(input_module, config_dict)
    osnma_r.start()

    base_logger, file_handler, log_filename = get_base_logger_and_file_handler()
    base_logger.removeHandler(file_handler)

    with open(log_filename, 'r') as log_file:
        log_text = log_file.read()

        tags_auth = len(re.findall(r'Tag AUTHENTICATED', log_text))
        data_auth = len(re.findall(r'INFO .* AUTHENTICATED: ADKD', log_text))
        kroot_auth = len(re.findall(r'INFO .*KROOT.*\n\tAUTHENTICATED\n', log_text))
        warnings = len(re.findall('WARNING', log_text))
        broken_kroot = len(re.findall('WARNING.*Broken HKROOT', log_text))
        crc_failed = len(re.findall('WARNING.*CRC', log_text))
        errors = len(re.findall('ERROR', log_text))

    assert tags_auth == 2349
    assert data_auth == 1499
    assert kroot_auth == 17
    assert crc_failed == 22
    assert broken_kroot == 5
    assert warnings == 28
    assert errors == 0


def test_sbf_config7(log_level=logging.INFO):
    config_dict = {
        'console_log_level': log_level,
        'logs_path': LOGS_PATH,
        'scenario_path': Path(__file__).parent / 'scenarios/config7/nominal_noheaders.csv',
        'exec_path': Path(__file__).parent / 'scenarios/config7/',
        'pubk_name': 'OSNMA_PublicKey_test.xml'
    }

    input_module = SBFAscii(config_dict['scenario_path'])
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
        warnings = len(re.findall('WARNING', log_text))
        errors = len(re.findall('ERROR', log_text))

    assert tags_auth == 4252
    assert data_auth == 2914
    assert kroot_auth == 53
    assert broken_kroot == 8
    assert warnings == 19
    assert errors == 0


def test_sbf_eoc_1(log_level=logging.INFO):
    config_dict = {
        'console_log_level': log_level,
        'logs_path': LOGS_PATH,
        'scenario_path': Path(__file__).parent / 'scenarios/eoc/eoc.sbf',
        'pubk_name': 'OSNMA_PublicKey_9.xml',
        'exec_path': Path(__file__).parent / 'scenarios/eoc/'
    }

    input_module = SBF(config_dict['scenario_path'])
    osnma_r = OSNMAReceiver(input_module, config_dict)
    osnma_r.start()

    base_logger, file_handler, log_filename = get_base_logger_and_file_handler()
    base_logger.removeHandler(file_handler)

    with open(log_filename, 'r') as log_file:
        log_text = log_file.read()

        tags_auth = len(re.findall(r'Tag AUTHENTICATED', log_text))
        data_auth = len(re.findall(r'INFO .* AUTHENTICATED: ADKD', log_text))
        kroot_auth = len(re.findall(r'INFO .*KROOT.*\n\tAUTHENTICATED\n', log_text))
        kroot_cid_2_auth = len(re.findall(r'INFO .*KROOT.*CID: 2.*\n\tAUTHENTICATED\n', log_text))
        kroot_cid_3_auth = len(re.findall(r'INFO .*KROOT.*CID: 3.*\n\tAUTHENTICATED\n', log_text))
        warnings = len(re.findall('WARNING', log_text))
        gps_prn_d = len(re.findall('WARNING.*PRN_D 64 - 95', log_text))
        crc_failed = len(re.findall('WARNING.*CRC', log_text))
        broken_kroot = len(re.findall('WARNING.*Broken HKROOT', log_text))
        errors = len(re.findall('ERROR', log_text))

    assert tags_auth == 3743
    assert data_auth == 1541
    assert kroot_auth == 33
    assert kroot_cid_2_auth == 16
    assert kroot_cid_3_auth == 17
    assert broken_kroot == 6
    assert gps_prn_d == 1376
    assert crc_failed == 4
    assert warnings == 1387
    assert errors == 0


def test_sbf_npk_1(log_level=logging.INFO):
    config_dict = {
        'console_log_level': log_level,
        'logs_path': LOGS_PATH,
        'scenario_path': Path(__file__).parent / 'scenarios/npk_1/npk_1.sbf',
        'pubk_name': 'OSNMA_PublicKey_3.xml',
        'exec_path': Path(__file__).parent / 'scenarios/npk_1/'
    }

    input_module = SBF(config_dict['scenario_path'])
    osnma_r = OSNMAReceiver(input_module, config_dict)
    osnma_r.start()

    base_logger, file_handler, log_filename = get_base_logger_and_file_handler()
    base_logger.removeHandler(file_handler)

    with open(log_filename, 'r') as log_file:
        log_text = log_file.read()

        tags_auth = len(re.findall(r'Tag AUTHENTICATED', log_text))
        data_auth = len(re.findall(r'INFO .* AUTHENTICATED: ADKD', log_text))
        kroot_auth = len(re.findall(r'INFO .*KROOT.*\n\tAUTHENTICATED\n', log_text))
        warnings = len(re.findall('WARNING', log_text))
        crc_failed = len(re.findall('WARNING.*CRC', log_text))
        broken_kroot = len(re.findall('WARNING.*Broken HKROOT', log_text))
        errors = len(re.findall('ERROR', log_text))

    assert tags_auth == 3839
    assert data_auth == 1323
    assert kroot_auth == 17
    assert broken_kroot == 6
    assert crc_failed == 0
    assert warnings == 7
    assert errors == 0


def test_sbf_npk_2(log_level=logging.INFO):
    config_dict = {
        'console_log_level': log_level,
        'logs_path': LOGS_PATH,
        'scenario_path': Path(__file__).parent / 'scenarios/npk_2/npk_2.sbf',
        'pubk_name': 'OSNMA_PublicKey_4.xml',
        'exec_path': Path(__file__).parent / 'scenarios/npk_2/'
    }

    input_module = SBF(config_dict['scenario_path'])
    osnma_r = OSNMAReceiver(input_module, config_dict)
    osnma_r.start()

    base_logger, file_handler, log_filename = get_base_logger_and_file_handler()
    base_logger.removeHandler(file_handler)

    with open(log_filename, 'r') as log_file:
        log_text = log_file.read()

        tags_auth = len(re.findall(r'Tag AUTHENTICATED', log_text))
        data_auth = len(re.findall(r'INFO .* AUTHENTICATED: ADKD', log_text))
        kroot_auth = len(re.findall(r'INFO .*KROOT.*\n\tAUTHENTICATED\n', log_text))
        warnings = len(re.findall('WARNING', log_text))
        crc_failed = len(re.findall('WARNING.*CRC', log_text))
        broken_kroot = len(re.findall('WARNING.*Broken HKROOT', log_text))
        errors = len(re.findall('ERROR', log_text))

    assert tags_auth == 4675
    assert data_auth == 1606
    assert kroot_auth == 17
    assert crc_failed == 8
    assert broken_kroot == 7
    assert warnings == 16
    assert errors == 0


def test_sbf_npk_12(log_level=logging.INFO):
    config_dict = {
        'console_log_level': log_level,
        'logs_path': LOGS_PATH,
        'scenario_path': Path(__file__).parent / 'scenarios/npk_12/npk_12_noheaders.csv',
        'pubk_name': 'OSNMA_PublicKey_3.xml',
        'exec_path': Path(__file__).parent / 'scenarios/npk_12/'
    }

    input_module = SBFAscii(config_dict['scenario_path'])
    osnma_r = OSNMAReceiver(input_module, config_dict)
    osnma_r.start()

    base_logger, file_handler, log_filename = get_base_logger_and_file_handler()
    base_logger.removeHandler(file_handler)

    with open(log_filename, 'r') as log_file:
        log_text = log_file.read()

        tags_auth = len(re.findall(r'Tag AUTHENTICATED', log_text))
        data_auth = len(re.findall(r'INFO .* AUTHENTICATED: ADKD', log_text))
        kroot_auth = len(re.findall(r'INFO .*KROOT.*\n\tAUTHENTICATED\n', log_text))
        warnings = len(re.findall('WARNING', log_text))
        crc_failed = len(re.findall('WARNING.*CRC', log_text))
        broken_kroot = len(re.findall('WARNING.*Broken HKROOT', log_text))
        errors = len(re.findall('ERROR', log_text))
        adkd4_failed = len(re.findall(r'ERROR.*Tag FAILED\n\t.*\(255, 4, 0\)', log_text))

    assert tags_auth == 3147
    assert data_auth == 911
    assert kroot_auth == 12
    assert broken_kroot == 6
    assert crc_failed == 0
    assert warnings == 7
    assert errors == 6
    assert adkd4_failed == 6


def test_sbf_pkrev_1(log_level=logging.INFO):
    config_dict = {
        'console_log_level': log_level,
        'logs_path': LOGS_PATH,
        'scenario_path': Path(__file__).parent / 'scenarios/pkrev_1/pkrev_1.sbf',
        'pubk_name': 'OSNMA_PublicKey_4.xml',
        'exec_path': Path(__file__).parent / 'scenarios/pkrev_1/'
    }

    input_module = SBF(config_dict['scenario_path'])
    osnma_r = OSNMAReceiver(input_module, config_dict)
    osnma_r.start()

    base_logger, file_handler, log_filename = get_base_logger_and_file_handler()
    base_logger.removeHandler(file_handler)

    with open(log_filename, 'r') as log_file:
        log_text = log_file.read()

        tags_auth = len(re.findall(r'Tag AUTHENTICATED', log_text))
        data_auth = len(re.findall(r'INFO .* AUTHENTICATED: ADKD', log_text))
        kroot_auth = len(re.findall(r'INFO .*KROOT.*\n\tAUTHENTICATED\n', log_text))
        kroot_4_auth = len(re.findall(r'INFO .*KROOT.*PKID: 4.*\n\tAUTHENTICATED\n', log_text))
        kroot_5_auth = len(re.findall(r'INFO .*KROOT.*PKID: 5.*\n\tAUTHENTICATED\n', log_text))
        warnings = len(re.findall('WARNING', log_text))
        crc_failed = len(re.findall('WARNING.*CRC', log_text))
        broken_kroot = len(re.findall('WARNING.*Broken HKROOT', log_text))
        nma_dont_use = len(re.findall(r'WARNING.*NMA.*Don\'t Use', log_text))
        errors = len(re.findall('ERROR', log_text))

    assert tags_auth == 3408
    assert data_auth == 1111
    assert kroot_auth == 28
    assert kroot_4_auth == 24
    assert kroot_5_auth == 4
    assert crc_failed == 11
    assert broken_kroot == 7
    assert warnings == 183
    assert nma_dont_use == 164
    assert errors == 0


def test_sbf_pkrev_2(log_level=logging.INFO):
    config_dict = {
        'console_log_level': log_level,
        'logs_path': LOGS_PATH,
        'scenario_path': Path(__file__).parent / 'scenarios/pkrev_2/pkrev_2.sbf',
        'exec_path': Path(__file__).parent / 'scenarios/pkrev_2/'
    }

    input_module = SBF(config_dict['scenario_path'])
    osnma_r = OSNMAReceiver(input_module, config_dict)
    osnma_r.start()

    base_logger, file_handler, log_filename = get_base_logger_and_file_handler()
    base_logger.removeHandler(file_handler)

    with open(log_filename, 'r') as log_file:
        log_text = log_file.read()

        tags_auth = len(re.findall(r'Tag AUTHENTICATED', log_text))
        data_auth = len(re.findall(r'INFO .* AUTHENTICATED: ADKD', log_text))
        kroot_auth = len(re.findall(r'INFO .*KROOT.*\n\tAUTHENTICATED\n', log_text))
        warnings = len(re.findall('WARNING', log_text))
        crc_failed = len(re.findall('WARNING.*CRC', log_text))
        broken_kroot = len(re.findall('WARNING.*Broken HKROOT', log_text))
        nma_dont_use = len(re.findall(r'WARNING.*NMA.*Don\'t Use', log_text))
        errors = len(re.findall('ERROR', log_text))

    assert tags_auth == 1066
    assert data_auth == 353
    assert kroot_auth == 10
    assert crc_failed == 17
    assert broken_kroot == 8
    assert warnings == 292
    assert nma_dont_use == 267
    assert errors == 0


def test_sbf_pkrev_2_with_pk(log_level=logging.INFO):
    config_dict = {
        'console_log_level': log_level,
        'logs_path': LOGS_PATH,
        'scenario_path': Path(__file__).parent / 'scenarios/pkrev_2_with_pk/pkrev_2.sbf',
        'pubk_name': 'OSNMA_PublicKey_5.xml',
        'exec_path': Path(__file__).parent / 'scenarios/pkrev_2_with_pk/'
    }

    input_module = SBF(config_dict['scenario_path'])
    osnma_r = OSNMAReceiver(input_module, config_dict)
    osnma_r.start()

    base_logger, file_handler, log_filename = get_base_logger_and_file_handler()
    base_logger.removeHandler(file_handler)

    with open(log_filename, 'r') as log_file:
        log_text = log_file.read()

        tags_auth = len(re.findall(r'Tag AUTHENTICATED', log_text))
        data_auth = len(re.findall(r'INFO .* AUTHENTICATED: ADKD', log_text))
        kroot_auth = len(re.findall(r'INFO .*KROOT.*\n\tAUTHENTICATED\n', log_text))
        warnings = len(re.findall('WARNING', log_text))
        crc_failed = len(re.findall('WARNING.*CRC', log_text))
        broken_kroot = len(re.findall('WARNING.*Broken HKROOT', log_text))
        nma_dont_use = len(re.findall(r'WARNING.*NMA.*Don\'t Use', log_text))
        errors = len(re.findall('ERROR', log_text))

    assert tags_auth == 1066
    assert data_auth == 353
    assert kroot_auth == 11
    assert crc_failed == 17
    assert broken_kroot == 8
    assert warnings == 386
    assert nma_dont_use == 360
    assert errors == 0


def test_sbf_pkrev_12(log_level=logging.INFO):
    config_dict = {
        'console_log_level': log_level,
        'logs_path': LOGS_PATH,
        'scenario_path': Path(__file__).parent / 'scenarios/pkrev_12/pkrev_12_noheaders.csv',
        'pubk_name': 'OSNMA_PublicKey_4.xml',
        'exec_path': Path(__file__).parent / 'scenarios/pkrev_12/'
    }

    input_module = SBFAscii(config_dict['scenario_path'])
    osnma_r = OSNMAReceiver(input_module, config_dict)
    osnma_r.start()

    base_logger, file_handler, log_filename = get_base_logger_and_file_handler()
    base_logger.removeHandler(file_handler)

    with open(log_filename, 'r') as log_file:
        log_text = log_file.read()

        tags_auth = len(re.findall(r'Tag AUTHENTICATED', log_text))
        data_auth = len(re.findall(r'INFO .* AUTHENTICATED: ADKD', log_text))
        kroot_auth = len(re.findall(r'INFO .*KROOT.*\n\tAUTHENTICATED\n', log_text))
        kroot_4_auth = len(re.findall(r'INFO .*KROOT.*PKID: 4.*\n\tAUTHENTICATED\n', log_text))
        kroot_5_auth = len(re.findall(r'INFO .*KROOT.*PKID: 5.*\n\tAUTHENTICATED\n', log_text))
        warnings = len(re.findall('WARNING', log_text))
        crc_failed = len(re.findall('WARNING.*CRC', log_text))
        broken_kroot = len(re.findall('WARNING.*Broken HKROOT', log_text))
        nma_dont_use = len(re.findall(r'WARNING.*NMA.*Don\'t Use', log_text))
        errors = len(re.findall('ERROR', log_text))

    assert tags_auth == 4474
    assert data_auth == 1477
    assert kroot_auth == 40
    assert kroot_4_auth == 24
    assert kroot_5_auth == 16
    assert crc_failed == 28
    assert broken_kroot == 15
    assert warnings == 585
    assert nma_dont_use == 541
    assert errors == 0


if __name__ == "__main__":

    general_log_level = logging.CRITICAL
    test_passed = 0
    test_done = 0

    print(f"\nStart Nominal Test Configuration 1")
    try:
        test_sbf_config1(general_log_level)
    except AssertionError:
        print(f"\tFAILED")
    else:
        test_passed += 1
        print(f"\tCORRECT")
    finally:
        test_done += 1

    print(f"\nStart Nominal Test Configuration 2")
    try:
        test_sbf_config2(general_log_level)
    except AssertionError:
        print(f"\tFAILED")
    else:
        test_passed += 1
        print(f"\tCORRECT")
    finally:
        test_done += 1

    print(f"\nStart Nominal Test Configuration 5")
    try:
        test_sbf_config5(general_log_level)
    except AssertionError:
        print(f"\tFAILED")
    else:
        test_passed += 1
        print(f"\tCORRECT")
    finally:
        test_done += 1


    print(f"\nStart End Of Chain - Step 1")
    try:
        test_sbf_eoc_1(general_log_level)
    except AssertionError:
        print(f"\tFAILED")
    else:
        test_passed += 1
        print(f"\tCORRECT")
    finally:
        test_done += 1


    print(f"\nStart New Public Key - Step 1")
    try:
        test_sbf_npk_1(general_log_level)
    except AssertionError:
        print(f"\tFAILED")
    else:
        test_passed += 1
        print(f"\tCORRECT")
    finally:
        test_done += 1

    print(f"\nStart New Public Key - Step 2")
    try:
        test_sbf_npk_2(general_log_level)
    except AssertionError:
        print(f"\tFAILED")
    else:
        test_passed += 1
        print(f"\tCORRECT")
    finally:
        test_done += 1

    print(f"\nStart New Public Key - Step 1 and Step 2")
    try:
        test_sbf_npk_12(general_log_level)
    except AssertionError:
        print(f"\tFAILED")
    else:
        test_passed += 1
        print(f"\tCORRECT")
    finally:
        test_done += 1


    print(f"\nStart Public Key Revoked - Transition to Step 1")
    try:
        test_sbf_pkrev_1(general_log_level)
    except AssertionError:
        print(f"\tFAILED")
    else:
        test_passed += 1
        print(f"\tCORRECT")
    finally:
        test_done += 1

    print(f"\nStart Public Key Revoked - Transition to Step 2")
    try:
        test_sbf_pkrev_2(general_log_level)
    except AssertionError:
        print(f"\tFAILED")
    else:
        test_passed += 1
        print(f"\tCORRECT")
    finally:
        test_done += 1

    print(f"\nStart Public Key Revoked - Transition to Step 2 with Public Key stored")
    try:
        test_sbf_pkrev_2_with_pk(general_log_level)
    except AssertionError:
        print(f"\tFAILED")
    else:
        test_passed += 1
        print(f"\tCORRECT")
    finally:
        test_done += 1

    print(f"\nStart Public Key Revoked - Transition to Step 1 and Step 2")
    try:
        test_sbf_pkrev_12(general_log_level)
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

