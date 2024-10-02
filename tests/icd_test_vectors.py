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


def get_base_logger_and_file_handler(logger_name):
    base_logger = logger_factory.get_logger(logger_name)
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

    general_logger, general_file_handler, general_log_filename = get_base_logger_and_file_handler('osnma')
    general_logger.removeHandler(general_file_handler)

    status_log_filename = general_log_filename.rpartition('/')[0] + '/' + 'status_log.json'

    with open(general_log_filename, 'r') as log_file:
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

    with open(status_log_filename, 'r') as log_file:
        log_text = log_file.read()

        total_subframes = len(re.findall(r'"GST_subframe":', log_text))
        nmas_operational = len(re.findall(r'\"nma_status\": \{\"nmas\": \"OPERATIONAL\"', log_text))
        nmas_test = len(re.findall(r'\"nma_status\": \{\"nmas\": \"TEST\"', log_text))
        nmas_dnu = len(re.findall(r'\"nma_status\": \{\"nmas\": \"DONT_USE\"', log_text))
        total_cpks_nominal = len(re.findall(r'\"nma_status\".*\"cpks\": \"NOMINAL\".*\"tesla_chain_in_force', log_text))
        total_npkid = len(re.findall(r'\"public_key_in_force\": \{\"npkid\"', log_text))
        # TBC

    # print(f"{total_subframes} vs {expected_results_dict['total_subframes']}")
    # print(f"{nmas_operational} vs {expected_results_dict['nmas_operational']}")
    # print(f"{nmas_test} vs {expected_results_dict['nmas_test']}")
    # print(f"{nmas_dnu} vs {expected_results_dict['nmas_dnu']}")
    # print(f"{total_cpks_nominal} vs {expected_results_dict['total_cpks_nominal']}")
    # print(f"{total_npkid} vs {expected_results_dict['total_npkid']}")

    assert total_subframes == expected_results_dict['total_subframes']
    assert nmas_operational == expected_results_dict['nmas_operational']
    assert nmas_test == expected_results_dict['nmas_test']
    assert nmas_dnu == expected_results_dict['nmas_dnu']
    assert total_cpks_nominal == expected_results_dict['total_cpks_nominal']
    assert total_npkid == expected_results_dict['total_npkid']

def test_vectors_icd_configuration_1(log_level=logging.INFO):
    config_dict = {
        'console_log_level': log_level,
        'logs_path': LOGS_PATH,
        'scenario_path': Path(__file__).parent / 'icd_test_vectors/configuration_1/16_AUG_2023_GST_05_00_01_fixed.csv',
        'exec_path': Path(__file__).parent / 'icd_test_vectors/configuration_1/',
        'pubk_name': 'OSNMA_PublicKey.xml',
        'do_status_log': True,
    }

    expected_results = {
        "tags_auth": 12532,
        "data_auth": 6144,
        "kroot_auth": 176,
        "broken_kroot": 0,
        "crc_failed": 0,
        "warnings": 0,
        "errors": 0,
        "total_subframes": 119,
        "nmas_operational": 0,
        "nmas_test": 118,
        "nmas_dnu": 0,
        "total_cpks_nominal": 118,
        "total_npkid": 118,
    }

    input_module = ICDTestVectors(config_dict['scenario_path'])
    run(input_module, config_dict, expected_results)

def test_vectors_icd_configuration_2(log_level=logging.INFO):
    config_dict = {
        'console_log_level': log_level,
        'logs_path': LOGS_PATH,
        'scenario_path': Path(__file__).parent / 'icd_test_vectors/configuration_2/27_JUL_2023_GST_00_00_01_fixed.csv',
        'exec_path': Path(__file__).parent / 'icd_test_vectors/configuration_2/',
        'do_status_log': True,
    }

    expected_results = {
        "tags_auth": 11427,
        "data_auth": 6056,
        "kroot_auth": 115,
        "broken_kroot": 17,  # The first page for all satellites has no OSNMA data
        "crc_failed": 0,
        "warnings": 17,
        "errors": 0,
        "total_subframes": 119,
        "nmas_operational": 105,
        "nmas_test": 0,
        "nmas_dnu": 0,
        "total_cpks_nominal": 105,
        "total_npkid": 105,
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
        'kroot_name': 'OSNMA_start_KROOT.txt',
        'do_status_log': True,
    }

    expected_results = {
        "tags_auth": 11427,
        "data_auth": 6056,
        "kroot_auth": 115,
        "broken_kroot": 17,  # The first page for all satellites has no OSNMA data
        "crc_failed": 0,
        "warnings": 17,
        "errors": 0,
        "total_subframes": 119,
        "nmas_operational": 119,
        "nmas_test": 0,
        "nmas_dnu": 0,
        "total_cpks_nominal": 119,
        "total_npkid": 119,
    }

    input_module = ICDTestVectors(config_dict['scenario_path'])
    run(input_module, config_dict, expected_results)

def test_vectors_eoc_step1(log_level=logging.INFO):
    config_dict = {
        'console_log_level': log_level,
        'logs_path': LOGS_PATH,
        'scenario_path': Path(__file__).parent / 'icd_test_vectors/eoc_step1/06_OCT_2023_GST_16_45_01_fixed.csv',
        'exec_path': Path(__file__).parent / 'icd_test_vectors/eoc_step1/',
        'pubk_name': 'OSNMA_PublicKey_PKID_7.xml',
        'do_status_log': True,
    }

    expected_results = {
        "tags_auth": 13638,
        "data_auth": 6504,
        "kroot_auth": 183,
        "broken_kroot": 0,
        "crc_failed": 0,
        "warnings": 0,
        "errors": 0,
        "total_subframes": 119,
        "nmas_operational": 119,
        "nmas_test": 0,
        "nmas_dnu": 0,
        "total_cpks_nominal": 60,
        "total_npkid": 119,
    }

    input_module = ICDTestVectors(config_dict['scenario_path'])
    run(input_module, config_dict, expected_results)

def test_vectors_eoc_step2(log_level=logging.INFO):
    config_dict = {
        'console_log_level': log_level,
        'logs_path': LOGS_PATH,
        'scenario_path': Path(__file__).parent / 'icd_test_vectors/eoc_step2/06_OCT_2023_GST_18_30_01_fixed.csv',
        'exec_path': Path(__file__).parent / 'icd_test_vectors/eoc_step2/',
        'pubk_name': 'OSNMA_PublicKey_PKID_7.xml',
        'do_status_log': True,
    }

    expected_results = {
        "tags_auth": 13200,
        "data_auth": 6237,
        "kroot_auth": 230,
        "broken_kroot": 0,
        "crc_failed": 0,
        "warnings": 0,
        "errors": 0,
        "total_subframes": 119,
        "nmas_operational": 119,
        "nmas_test": 0,
        "nmas_dnu": 0,
        "total_cpks_nominal": 59,
        "total_npkid": 115,
    }

    input_module = ICDTestVectors(config_dict['scenario_path'])
    run(input_module, config_dict, expected_results)

def test_vectors_crev_step1(log_level=logging.INFO):
    config_dict = {
        'console_log_level': log_level,
        'logs_path': LOGS_PATH,
        'scenario_path': Path(__file__).parent / 'icd_test_vectors/crev_step1/06_OCT_2023_GST_21_45_01_fixed.csv',
        'exec_path': Path(__file__).parent / 'icd_test_vectors/crev_step1/',
        'pubk_name': 'OSNMA_PublicKey_PKID_7.xml',
        'do_status_log': True,
    }

    expected_results = {
        "tags_auth": 6600,
        "data_auth": 3120,
        "kroot_auth": 233,
        "broken_kroot": 0,
        "crc_failed": 0,
        "warnings": 1187,
        "errors": 0,
        "total_subframes": 119,
        "nmas_operational": 60,
        "nmas_test": 0,
        "nmas_dnu": 59,
        "total_cpks_nominal": 60,
        "total_npkid": 119,
    }

    input_module = ICDTestVectors(config_dict['scenario_path'])
    run(input_module, config_dict, expected_results)

def test_vectors_crev_step2(log_level=logging.INFO):
    config_dict = {
        'console_log_level': log_level,
        'logs_path': LOGS_PATH,
        'scenario_path': Path(__file__).parent / 'icd_test_vectors/crev_step2/06_OCT_2023_GST_23_30_01_fixed.csv',
        'exec_path': Path(__file__).parent / 'icd_test_vectors/crev_step2/',
        'pubk_name': 'OSNMA_PublicKey_PKID_7.xml',
        'do_status_log': True,
    }

    expected_results = {
        "tags_auth": 6547,
        "data_auth": 3095,
        "kroot_auth": 123,
        "broken_kroot": 0,
        "crc_failed": 0,
        "warnings": 1187,
        "errors": 0,
        "total_subframes": 119,
        "nmas_operational": 59,
        "nmas_test": 0,
        "nmas_dnu": 60,
        "total_cpks_nominal": 0,
        "total_npkid": 119,
    }

    input_module = ICDTestVectors(config_dict['scenario_path'])
    run(input_module, config_dict, expected_results)

def test_vectors_crev_step3(log_level=logging.INFO):
    config_dict = {
        'console_log_level': log_level,
        'logs_path': LOGS_PATH,
        'scenario_path': Path(__file__).parent / 'icd_test_vectors/crev_step3/07_OCT_2023_GST_00_30_01_fixed.csv',
        'exec_path': Path(__file__).parent / 'icd_test_vectors/crev_step3/',
        'pubk_name': 'OSNMA_PublicKey_PKID_7.xml',
        'do_status_log': True,
    }

    expected_results = {
        "tags_auth": 13601,
        "data_auth": 6514,
        "kroot_auth": 198,
        "broken_kroot": 0,
        "crc_failed": 0,
        "warnings": 0,
        "errors": 0,
        "total_subframes": 119,
        "nmas_operational": 116,
        "nmas_test": 0,
        "nmas_dnu": 0,
        "total_cpks_nominal": 59,
        "total_npkid": 116,
    }

    input_module = ICDTestVectors(config_dict['scenario_path'])
    run(input_module, config_dict, expected_results)

def test_vectors_npk_step1(log_level=logging.INFO):
    config_dict = {
        'console_log_level': log_level,
        'logs_path': LOGS_PATH,
        'scenario_path': Path(__file__).parent / 'icd_test_vectors/npk_step1/07_OCT_2023_GST_02_45_01_fixed.csv',
        'exec_path': Path(__file__).parent / 'icd_test_vectors/npk_step1/',
        'pubk_name': 'OSNMA_PublicKey_PKID_7.xml',
        'do_status_log': True,
    }

    expected_results = {
        "tags_auth": 12852,
        "data_auth": 6337,
        "kroot_auth": 146,
        "broken_kroot": 0,
        "crc_failed": 0,
        "warnings": 0,
        "errors": 0,
        "total_subframes": 119,
        "nmas_operational": 119,
        "nmas_test": 0,
        "nmas_dnu": 0,
        "total_cpks_nominal": 60,
        "total_npkid": 119,
    }

    input_module = ICDTestVectors(config_dict['scenario_path'])
    run(input_module, config_dict, expected_results)

def test_vectors_npk_step2(log_level=logging.INFO):
    config_dict = {
        'console_log_level': log_level,
        'logs_path': LOGS_PATH,
        'scenario_path': Path(__file__).parent / 'icd_test_vectors/npk_step2/07_OCT_2023_GST_03_45_01_fixed.csv',
        'exec_path': Path(__file__).parent / 'icd_test_vectors/npk_step2/',
        'pubk_name': 'OSNMA_PublicKey_PKID_7.xml',
        'do_status_log': True,
    }

    expected_results = {
        "tags_auth": 13566,
        "data_auth": 6487,
        "kroot_auth": 101,
        "broken_kroot": 0,
        "crc_failed": 0,
        "warnings": 0,
        "errors": 0,
        "total_subframes": 119,
        "nmas_operational": 116,
        "nmas_test": 0,
        "nmas_dnu": 0,
        "total_cpks_nominal": 0,
        "total_npkid": 116,
    }

    input_module = ICDTestVectors(config_dict['scenario_path'])
    run(input_module, config_dict, expected_results)

def test_vectors_npk_step3(log_level=logging.INFO):
    config_dict = {
        'console_log_level': log_level,
        'logs_path': LOGS_PATH,
        'scenario_path': Path(__file__).parent / 'icd_test_vectors/npk_step3/07_OCT_2023_GST_04_45_01_fixed.csv',
        'exec_path': Path(__file__).parent / 'icd_test_vectors/npk_step3/',
        'pubk_name': 'OSNMA_PublicKey_PKID_8.xml',
        'do_status_log': True,
    }

    expected_results = {
        "tags_auth": 13475,
        "data_auth": 6472,
        "kroot_auth": 160,
        "broken_kroot": 0,
        "crc_failed": 0,
        "warnings": 0,
        "errors": 0,
        "total_subframes": 119,
        "nmas_operational": 116,
        "nmas_test": 0,
        "nmas_dnu": 0,
        "total_cpks_nominal": 59,
        "total_npkid": 116,
    }

    input_module = ICDTestVectors(config_dict['scenario_path'])
    run(input_module, config_dict, expected_results)

def test_vectors_pkrev_step1(log_level=logging.INFO):
    config_dict = {
        'console_log_level': log_level,
        'logs_path': LOGS_PATH,
        'scenario_path': Path(__file__).parent / 'icd_test_vectors/pkrev_step1/07_OCT_2023_GST_07_45_01_fixed.csv',
        'exec_path': Path(__file__).parent / 'icd_test_vectors/pkrev_step1/',
        'pubk_name': 'OSNMA_PublicKey_PKID_8.xml',
        'do_status_log': True,
    }

    expected_results = {
        "tags_auth": 6664,
        "data_auth": 3095,
        "kroot_auth": 117,
        "broken_kroot": 0,
        "crc_failed": 0,
        "warnings": 1150,
        "errors": 0,
        "total_subframes": 119,
        "nmas_operational": 61,
        "nmas_test": 0,
        "nmas_dnu": 58,
        "total_cpks_nominal": 77,
        "total_npkid": 119,
    }

    input_module = ICDTestVectors(config_dict['scenario_path'])
    run(input_module, config_dict, expected_results)

def test_vectors_pkrev_step2(log_level=logging.INFO):
    config_dict = {
        'console_log_level': log_level,
        'logs_path': LOGS_PATH,
        'scenario_path': Path(__file__).parent / 'icd_test_vectors/pkrev_step2/07_OCT_2023_GST_09_30_01_fixed.csv',
        'exec_path': Path(__file__).parent / 'icd_test_vectors/pkrev_step2/',
        'pubk_name': 'OSNMA_PublicKey_PKID_9.xml',
        'do_status_log': True,
    }

    expected_results = {
        "tags_auth": 4644,
        "data_auth": 2155,
        "kroot_auth": 56,
        "broken_kroot": 0,
        "crc_failed": 0,
        "warnings": 1281,
        "errors": 0,
        "total_subframes": 119,
        "nmas_operational": 42,
        "nmas_test": 0,
        "nmas_dnu": 65,
        "total_cpks_nominal": 0,
        "total_npkid": 107,
    }

    input_module = ICDTestVectors(config_dict['scenario_path'])
    run(input_module, config_dict, expected_results)

def test_vectors_pkrev_step3(log_level=logging.INFO):
    config_dict = {
        'console_log_level': log_level,
        'logs_path': LOGS_PATH,
        'scenario_path': Path(__file__).parent / 'icd_test_vectors/pkrev_step3/07_OCT_2023_GST_10_30_01_fixed.csv',
        'exec_path': Path(__file__).parent / 'icd_test_vectors/pkrev_step3/',
        'pubk_name': 'OSNMA_PublicKey_PKID_9.xml',
        'do_status_log': True,
    }

    expected_results = {
        "tags_auth": 13670,
        "data_auth": 6521,
        "kroot_auth": 86,
        "broken_kroot": 0,
        "crc_failed": 0,
        "warnings": 0,
        "errors": 0,
        "total_subframes": 119,
        "nmas_operational": 104,
        "nmas_test": 0,
        "nmas_dnu": 0,
        "total_cpks_nominal": 58,
        "total_npkid": 104,
    }

    input_module = ICDTestVectors(config_dict['scenario_path'])
    run(input_module, config_dict, expected_results)

def test_vectors_nmt_step1(log_level=logging.INFO):
    config_dict = {
        'console_log_level': log_level,
        'logs_path': LOGS_PATH,
        'scenario_path': Path(__file__).parent / 'icd_test_vectors/nmt_step1/07_OCT_2023_GST_12_45_01_fixed.csv',
        'exec_path': Path(__file__).parent / 'icd_test_vectors/nmt_step1/',
        'pubk_name': 'OSNMA_PublicKey_PKID_9.xml',
        'do_status_log': True,
    }

    expected_results = {
        "tags_auth": 13680,
        "data_auth": 6523,
        "kroot_auth": 92,
        "broken_kroot": 0,
        "crc_failed": 0,
        "warnings": 1,
        "errors": 0,
        "total_subframes": 119,
        "nmas_operational": 119,
        "nmas_test": 0,
        "nmas_dnu": 0,
        "total_cpks_nominal": 60,
        "total_npkid": 119,
    }

    input_module = ICDTestVectors(config_dict['scenario_path'])
    run(input_module, config_dict, expected_results)

def test_vectors_nmt_step2(log_level=logging.INFO):
    config_dict = {
        'console_log_level': log_level,
        'logs_path': LOGS_PATH,
        'scenario_path': Path(__file__).parent / 'icd_test_vectors/nmt_step2/07_OCT_2023_GST_13_45_01_fixed.csv',
        'exec_path': Path(__file__).parent / 'icd_test_vectors/nmt_step2/',
        'pubk_name': 'OSNMA_PublicKey_PKID_9.xml',
        'do_status_log': True,
    }

    expected_results = {
        "tags_auth": 13566,
        "data_auth": 6487,
        "kroot_auth": 68,
        "broken_kroot": 0,
        "crc_failed": 0,
        "warnings": 1,
        "errors": 0,
        "total_subframes": 119,
        "nmas_operational": 119,
        "nmas_test": 0,
        "nmas_dnu": 0,
        "total_cpks_nominal": 0,
        "total_npkid": 119,
    }

    input_module = ICDTestVectors(config_dict['scenario_path'])
    run(input_module, config_dict, expected_results)

def test_vectors_nmt_step3(log_level=logging.INFO):
    config_dict = {
        'console_log_level': log_level,
        'logs_path': LOGS_PATH,
        'scenario_path': Path(__file__).parent / 'icd_test_vectors/nmt_step3/07_OCT_2023_GST_14_45_01_fixed.csv',
        'exec_path': Path(__file__).parent / 'icd_test_vectors/nmt_step3/',
        'pubk_name': 'OSNMA_PublicKey_PKID_1.xml',
        'do_status_log': True,
    }

    expected_results = {
        "tags_auth": 13050,
        "data_auth": 6405,
        "kroot_auth": 140,
        "broken_kroot": 0,
        "crc_failed": 0,
        "warnings": 0,
        "errors": 0,
        "total_subframes": 119,
        "nmas_operational": 116,
        "nmas_test": 0,
        "nmas_dnu": 0,
        "total_cpks_nominal": 59,
        "total_npkid": 116,
    }

    input_module = ICDTestVectors(config_dict['scenario_path'])
    run(input_module, config_dict, expected_results)

def test_vectors_oam_step1(log_level=logging.INFO):
    config_dict = {
        'console_log_level': log_level,
        'logs_path': LOGS_PATH,
        'scenario_path': Path(__file__).parent / 'icd_test_vectors/oam_step1/07_OCT_2023_GST_18_45_01_fixed.csv',
        'exec_path': Path(__file__).parent / 'icd_test_vectors/oam_step1/',
        'pubk_name': 'OSNMA_PublicKey_1.xml',
        'do_status_log': True,
    }

    expected_results = {
        "tags_auth": 6549,
        "data_auth": 3096,
        "kroot_auth": 109,
        "broken_kroot": 0,
        "crc_failed": 0,
        "warnings": 2341,
        "errors": 0,
        "total_subframes": 119,
        "nmas_operational": 61,
        "nmas_test": 0,
        "nmas_dnu": 58,
        "total_cpks_nominal": 61,
        "total_npkid": 119,
    }

    input_module = ICDTestVectors(config_dict['scenario_path'])
    run(input_module, config_dict, expected_results)

def test_vectors_oam_step2(log_level=logging.INFO):
    config_dict = {
        'console_log_level': log_level,
        'logs_path': LOGS_PATH,
        'scenario_path': Path(__file__).parent / 'icd_test_vectors/oam_step2/07_OCT_2023_GST_19_45_01_fixed.csv',
        'exec_path': Path(__file__).parent / 'icd_test_vectors/oam_step2/',
        'pubk_name': 'OSNMA_PublicKey_1.xml',
        'do_status_log': True,
    }

    expected_results = {
        "tags_auth": 0,
        "data_auth": 0,
        "kroot_auth": 1,
        "broken_kroot": 20,
        "crc_failed": 0,
        "warnings": 2290,
        "errors": 0,
        "total_subframes": 119,
        "nmas_operational": 0,
        "nmas_test": 0,
        "nmas_dnu": 119,
        "total_cpks_nominal": 0,
        "total_npkid": 0,
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

    print(f"\nEnd Of Chain - Step 1")
    try:
        test_vectors_eoc_step1(general_log_level)
    except AssertionError:
        print(f"\tFAILED")
    else:
        test_passed += 1
        print(f"\tCORRECT")
    finally:
        test_done += 1

    print(f"\nEnd Of Chain - Step 2")
    try:
        test_vectors_eoc_step2(general_log_level)
    except AssertionError:
        print(f"\tFAILED")
    else:
        test_passed += 1
        print(f"\tCORRECT")
    finally:
        test_done += 1

    print(f"\nChain Revocation - Step 1")
    try:
        test_vectors_crev_step1(general_log_level)
    except AssertionError:
        print(f"\tFAILED")
    else:
        test_passed += 1
        print(f"\tCORRECT")
    finally:
        test_done += 1

    print(f"\nChain Revocation - Step 2")
    try:
        test_vectors_crev_step2(general_log_level)
    except AssertionError:
        print(f"\tFAILED")
    else:
        test_passed += 1
        print(f"\tCORRECT")
    finally:
        test_done += 1

    print(f"\nChain Revocation - Step 3")
    try:
        test_vectors_crev_step3(general_log_level)
    except AssertionError:
        print(f"\tFAILED")
    else:
        test_passed += 1
        print(f"\tCORRECT")
    finally:
        test_done += 1

    print(f"\nPublic Key Renewal - Step 1")
    try:
        test_vectors_npk_step1(general_log_level)
    except AssertionError:
        print(f"\tFAILED")
    else:
        test_passed += 1
        print(f"\tCORRECT")
    finally:
        test_done += 1

    print(f"\nPublic Key Renewal - Step 2")
    try:
        test_vectors_npk_step2(general_log_level)
    except AssertionError:
        print(f"\tFAILED")
    else:
        test_passed += 1
        print(f"\tCORRECT")
    finally:
        test_done += 1

    print(f"\nPublic Key Renewal - Step 3")
    try:
        test_vectors_npk_step3(general_log_level)
    except AssertionError:
        print(f"\tFAILED")
    else:
        test_passed += 1
        print(f"\tCORRECT")
    finally:
        test_done += 1

    print(f"\nPublic Key Revocation - Step 1")
    try:
        test_vectors_pkrev_step1(general_log_level)
    except AssertionError:
        print(f"\tFAILED")
    else:
        test_passed += 1
        print(f"\tCORRECT")
    finally:
        test_done += 1

    print(f"\nPublic Key Revocation - Step 2")
    try:
        test_vectors_pkrev_step2(general_log_level)
    except AssertionError:
        print(f"\tFAILED")
    else:
        test_passed += 1
        print(f"\tCORRECT")
    finally:
        test_done += 1

    print(f"\nPublic Key Revocation - Step 3")
    try:
        test_vectors_pkrev_step3(general_log_level)
    except AssertionError:
        print(f"\tFAILED")
    else:
        test_passed += 1
        print(f"\tCORRECT")
    finally:
        test_done += 1

    print(f"\nMerkle Tree Renewal - Step 1")
    try:
        test_vectors_nmt_step1(general_log_level)
    except AssertionError:
        print(f"\tFAILED")
    else:
        test_passed += 1
        print(f"\tCORRECT")
    finally:
        test_done += 1

    print(f"\nMerkle Tree Renewal - Step 2")
    try:
        test_vectors_nmt_step2(general_log_level)
    except AssertionError:
        print(f"\tFAILED")
    else:
        test_passed += 1
        print(f"\tCORRECT")
    finally:
        test_done += 1

    print(f"\nMerkle Tree Renewal - Step 3")
    try:
        test_vectors_nmt_step3(general_log_level)
    except AssertionError:
        print(f"\tFAILED")
    else:
        test_passed += 1
        print(f"\tCORRECT")
    finally:
        test_done += 1

    print(f"\nOSNMA Alert Message - Step 1")
    try:
        test_vectors_oam_step1(general_log_level)
    except AssertionError:
        print(f"\tFAILED")
    else:
        test_passed += 1
        print(f"\tCORRECT")
    finally:
        test_done += 1

    print(f"\nOSNMA Alert Message - Step 2")
    try:
        test_vectors_oam_step2(general_log_level)
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
