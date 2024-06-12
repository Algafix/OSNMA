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
LOGS_PATH = Path(__file__).parent / 'logs/idd_test_logs/'

from osnma.utils.config import Config
from osnma.utils.idd import IDD


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

def run(input_module, config_dict, expected_results_dict, num):

    Config.load_configuration_parameters(config_dict)
    logger_factory.configure_loggers()

    idd = IDD()


    base_logger, file_handler, log_filename = get_base_logger_and_file_handler()
    base_logger.removeHandler(file_handler)
    
    

    with open(log_filename, 'r') as log_file:
        log_text = log_file.read()

        warnings = len(re.findall('WARNING', log_text))
        errors = len(re.findall('ERROR', log_text))

    log_filename_correct = f"{Path(__file__).parent}" + '/idd_test_vectors/log/logs_' + f"{num}" +".log"

    with open(log_filename_correct, 'r') as log_file:
        log_text_correct = log_file.read()

    assert log_text == log_text_correct
    assert warnings == expected_results_dict["warnings"]
    assert errors == expected_results_dict["errors"]

def test_vectors_idd_configuration(log_level=logging.INFO):
    config_dict = {
        'console_log_level': log_level,
        'logs_path': LOGS_PATH,
        'scenario_path': Path(__file__).parent / 'icd_test_vectors/configuration_1/16_AUG_2023_GST_05_00_01_fixed.csv',
        'exec_path': Path(__file__).parent / 'idd_test_vectors/',
        'download_pki': True,
        'download_merkle': True,
        'download_ica': True,
        'download_sca': True,
        'download_rca': True,
        'CERT_FOLDER' : Path(__file__).parent / 'idd_test_vectors/Cert/'
    }

    expected_results = {
        "warnings": 0,
        "errors": 0
    }

    input_module = ICDTestVectors(config_dict['scenario_path'])
    run(input_module, config_dict, expected_results,1)

def test_vectors_idd_configuration_Good(log_level=logging.INFO):
    config_dict = {
        'console_log_level': log_level,
        'logs_path': LOGS_PATH,
        'scenario_path': Path(__file__).parent / 'icd_test_vectors/configuration_1/16_AUG_2023_GST_05_00_01_fixed.csv',
        'exec_path': Path(__file__).parent / 'idd_test_vectors/',
        'download_pki': False,
        'download_merkle': False,
        'download_sca': False,
        'download_rca': False,
        'CERT_FOLDER' : Path(__file__).parent / 'idd_test_vectors/',
        'USER_IDD_CERT' : {
            "CERT_PKIEE" : "Cert 4 - PKI/pki.crt",
            "CERT_MERKLE" : "Cert 4 - MK/mk.crt",
            "CERT_ICA" : "Cert 3- ICA/ica.crt",
            "CERT_SCA" : "Cert 2 - SCA/sca.crt",
            "CERT_RCA" : "Cert 1 - RCA/rca.crt"
        },

        'USER_IDD_CRL' : {
            "CRL_ICA" : 'CRL 3 - ICA/ica.crl',
            "CRL_SCA" : 'CRL 2 - SCA/sca.crl',
            "CRL_RCA" : 'CRL 1 - RCA/rca.crl'
        },
        "MERKLE_NAME" : Path(__file__).parent / "idd_test_vectors/Cert/OSNMA_MerkleTree_20240115100000_newPKID_1.xml"
    }

    expected_results = {
        "warnings": 0,
        "errors": 0
    }

    input_module = ICDTestVectors(config_dict['scenario_path'])
    run(input_module, config_dict, expected_results,2)

def test_vectors_idd_configuration_cert_1_time(log_level=logging.INFO):
    config_dict = {
        'console_log_level': log_level,
        'logs_path': LOGS_PATH,
        'scenario_path': Path(__file__).parent / 'icd_test_vectors/configuration_1/16_AUG_2023_GST_05_00_01_fixed.csv',
        'exec_path': Path(__file__).parent / 'idd_test_vectors/',
        'download_pki': False,
        'download_merkle': False,
        'download_sca': False,
        'download_rca': False,
        'CERT_FOLDER' : Path(__file__).parent / 'idd_test_vectors/',
        'USER_IDD_CERT' : {
            "CERT_PKIEE" : "Cert 4 - PKI/pki.crt",
            "CERT_MERKLE" : "Cert 4 - MK/mk.crt",
            "CERT_ICA" : "Cert 3- ICA/ica.crt",
            "CERT_SCA" : "Cert 2 - SCA/sca.crt",
            "CERT_RCA" : "Cert 1 - RCA/rca_time.crt"
        },

        'USER_IDD_CRL' : {
            "CRL_ICA" : 'CRL 3 - ICA/ica.crl',
            "CRL_SCA" : 'CRL 2 - SCA/sca.crl',
            "CRL_RCA" : 'CRL 1 - RCA/rca.crl'
        },
        "MERKLE_NAME" : Path(__file__).parent / "idd_test_vectors/Cert/OSNMA_MerkleTree_20240115100000_newPKID_1.xml"
    }

    expected_results = {
        "warnings": 1,
        "errors": 0
    }

    input_module = ICDTestVectors(config_dict['scenario_path'])
    run(input_module, config_dict, expected_results,3)

def test_vectors_idd_configuration_cert_1_issuer(log_level=logging.INFO):
    config_dict = {
        'console_log_level': log_level,
        'logs_path': LOGS_PATH,
        'scenario_path': Path(__file__).parent / 'icd_test_vectors/configuration_1/16_AUG_2023_GST_05_00_01_fixed.csv',
        'exec_path': Path(__file__).parent / 'idd_test_vectors/',
        'download_pki': False,
        'download_merkle': False,
        'download_sca': False,
        'download_rca': False,
        'CERT_FOLDER' : Path(__file__).parent / 'idd_test_vectors/',
        'USER_IDD_CERT' : {
            "CERT_PKIEE" : "Cert 4 - PKI/pki.crt",
            "CERT_MERKLE" : "Cert 4 - MK/mk.crt",
            "CERT_ICA" : "Cert 3- ICA/ica.crt",
            "CERT_SCA" : "Cert 2 - SCA/sca.crt",
            "CERT_RCA" : "Cert 1 - RCA/rca_issuer.crt"
        },

        'USER_IDD_CRL' : {
            "CRL_ICA" : 'CRL 3 - ICA/ica.crl',
            "CRL_SCA" : 'CRL 2 - SCA/sca.crl',
            "CRL_RCA" : 'CRL 1 - RCA/rca.crl'
        },
        "MERKLE_NAME" : Path(__file__).parent / "idd_test_vectors/Cert/OSNMA_MerkleTree_20240115100000_newPKID_1.xml"
    }

    expected_results = {
        "warnings": 1,
        "errors": 0
    }

    input_module = ICDTestVectors(config_dict['scenario_path'])
    run(input_module, config_dict, expected_results,4)

def test_vectors_idd_configuration_cert_1_signature(log_level=logging.INFO):
    config_dict = {
        'console_log_level': log_level,
        'logs_path': LOGS_PATH,
        'scenario_path': Path(__file__).parent / 'icd_test_vectors/configuration_1/16_AUG_2023_GST_05_00_01_fixed.csv',
        'exec_path': Path(__file__).parent / 'idd_test_vectors/',
        'download_pki': False,
        'download_merkle': False,
        'download_sca': False,
        'download_rca': False,
        'CERT_FOLDER' : Path(__file__).parent / 'idd_test_vectors/',
        'USER_IDD_CERT' : {
            "CERT_PKIEE" : "Cert 4 - PKI/pki.crt",
            "CERT_MERKLE" : "Cert 4 - MK/mk.crt",
            "CERT_ICA" : "Cert 3- ICA/ica.crt",
            "CERT_SCA" : "Cert 2 - SCA/sca.crt",
            "CERT_RCA" : "Cert 1 - RCA/rca_signature.crt"
        },

        'USER_IDD_CRL' : {
            "CRL_ICA" : 'CRL 3 - ICA/ica.crl',
            "CRL_SCA" : 'CRL 2 - SCA/sca.crl',
            "CRL_RCA" : 'CRL 1 - RCA/rca.crl'
        },
        "MERKLE_NAME" : Path(__file__).parent / "idd_test_vectors/Cert/OSNMA_MerkleTree_20240115100000_newPKID_1.xml"
    }

    expected_results = {
        "warnings": 1,
        "errors": 0
    }

    input_module = ICDTestVectors(config_dict['scenario_path'])
    run(input_module, config_dict, expected_results,5)

def test_vectors_idd_configuration_cert_2_time(log_level=logging.INFO):
    config_dict = {
        'console_log_level': log_level,
        'logs_path': LOGS_PATH,
        'scenario_path': Path(__file__).parent / 'icd_test_vectors/configuration_1/16_AUG_2023_GST_05_00_01_fixed.csv',
        'exec_path': Path(__file__).parent / 'idd_test_vectors/',
        'download_pki': False,
        'download_merkle': False,
        'download_sca': False,
        'download_rca': False,
        'CERT_FOLDER' : Path(__file__).parent / 'idd_test_vectors/',
        'USER_IDD_CERT' : {
            "CERT_PKIEE" : "Cert 4 - PKI/pki.crt",
            "CERT_MERKLE" : "Cert 4 - MK/mk.crt",
            "CERT_ICA" : "Cert 3- ICA/ica.crt",
            "CERT_SCA" : "Cert 2 - SCA/sca_time.crt",
            "CERT_RCA" : "Cert 1 - RCA/rca.crt"
        },

        'USER_IDD_CRL' : {
            "CRL_ICA" : 'CRL 3 - ICA/ica.crl',
            "CRL_SCA" : 'CRL 2 - SCA/sca.crl',
            "CRL_RCA" : 'CRL 1 - RCA/rca.crl'
        },
        "MERKLE_NAME" : Path(__file__).parent / "idd_test_vectors/Cert/OSNMA_MerkleTree_20240115100000_newPKID_1.xml"
    }

    expected_results = {
        "warnings": 1,
        "errors": 0
    }

    input_module = ICDTestVectors(config_dict['scenario_path'])
    run(input_module, config_dict, expected_results,6)

def test_vectors_idd_configuration_cert_2_issuer(log_level=logging.INFO):
    config_dict = {
        'console_log_level': log_level,
        'logs_path': LOGS_PATH,
        'scenario_path': Path(__file__).parent / 'icd_test_vectors/configuration_1/16_AUG_2023_GST_05_00_01_fixed.csv',
        'exec_path': Path(__file__).parent / 'idd_test_vectors/',
        'download_pki': False,
        'download_merkle': False,
        'download_sca': False,
        'download_rca': False,
        'CERT_FOLDER' : Path(__file__).parent / 'idd_test_vectors/',
        'USER_IDD_CERT' : {
            "CERT_PKIEE" : "Cert 4 - PKI/pki.crt",
            "CERT_MERKLE" : "Cert 4 - MK/mk.crt",
            "CERT_ICA" : "Cert 3- ICA/ica.crt",
            "CERT_SCA" : "Cert 2 - SCA/sca_issuer.crt",
            "CERT_RCA" : "Cert 1 - RCA/rca.crt"
        },

        'USER_IDD_CRL' : {
            "CRL_ICA" : 'CRL 3 - ICA/ica.crl',
            "CRL_SCA" : 'CRL 2 - SCA/sca.crl',
            "CRL_RCA" : 'CRL 1 - RCA/rca.crl'
        },
        "MERKLE_NAME" : Path(__file__).parent / "idd_test_vectors/Cert/OSNMA_MerkleTree_20240115100000_newPKID_1.xml"
    }

    expected_results = {
        "warnings": 1,
        "errors": 0
    }

    input_module = ICDTestVectors(config_dict['scenario_path'])
    run(input_module, config_dict, expected_results,7)

def test_vectors_idd_configuration_cert_2_signature(log_level=logging.INFO):
    config_dict = {
        'console_log_level': log_level,
        'logs_path': LOGS_PATH,
        'scenario_path': Path(__file__).parent / 'icd_test_vectors/configuration_1/16_AUG_2023_GST_05_00_01_fixed.csv',
        'exec_path': Path(__file__).parent / 'idd_test_vectors/',
        'download_pki': False,
        'download_merkle': False,
        'download_sca': False,
        'download_rca': False,
        'CERT_FOLDER' : Path(__file__).parent / 'idd_test_vectors/',
        'USER_IDD_CERT' : {
            "CERT_PKIEE" : "Cert 4 - PKI/pki.crt",
            "CERT_MERKLE" : "Cert 4 - MK/mk.crt",
            "CERT_ICA" : "Cert 3- ICA/ica.crt",
            "CERT_SCA" : "Cert 2 - SCA/sca_signature.crt",
            "CERT_RCA" : "Cert 1 - RCA/rca.crt"
        },

        'USER_IDD_CRL' : {
            "CRL_ICA" : 'CRL 3 - ICA/ica.crl',
            "CRL_SCA" : 'CRL 2 - SCA/sca.crl',
            "CRL_RCA" : 'CRL 1 - RCA/rca.crl'
        },
        "MERKLE_NAME" : Path(__file__).parent / "idd_test_vectors/Cert/OSNMA_MerkleTree_20240115100000_newPKID_1.xml"
    }

    expected_results = {
        "warnings": 1,
        "errors": 0
    }

    input_module = ICDTestVectors(config_dict['scenario_path'])
    run(input_module, config_dict, expected_results,8)

def test_vectors_idd_configuration_cert_2_revokated(log_level=logging.INFO):
    config_dict = {
        'console_log_level': log_level,
        'logs_path': LOGS_PATH,
        'scenario_path': Path(__file__).parent / 'icd_test_vectors/configuration_1/16_AUG_2023_GST_05_00_01_fixed.csv',
        'exec_path': Path(__file__).parent / 'idd_test_vectors/',
        'download_pki': False,
        'download_merkle': False,
        'download_sca': False,
        'download_rca': False,
        'CERT_FOLDER' : Path(__file__).parent / 'idd_test_vectors/',
        'USER_IDD_CERT' : {
            "CERT_PKIEE" : "Cert 4 - PKI/pki.crt",
            "CERT_MERKLE" : "Cert 4 - MK/mk.crt",
            "CERT_ICA" : "Cert 3- ICA/ica.crt",
            "CERT_SCA" : "Cert 2 - SCA/sca.crt",
            "CERT_RCA" : "Cert 1 - RCA/rca.crt"
        },

        'USER_IDD_CRL' : {
            "CRL_ICA" : 'CRL 3 - ICA/ica.crl',
            "CRL_SCA" : 'CRL 2 - SCA/sca.crl',
            "CRL_RCA" : 'CRL 1 - RCA/rca_revokated.crl'
        },
        "MERKLE_NAME" : Path(__file__).parent / "idd_test_vectors/Cert/OSNMA_MerkleTree_20240115100000_newPKID_1.xml"
    }

    expected_results = {
        "warnings": 1,
        "errors": 0
    }

    input_module = ICDTestVectors(config_dict['scenario_path'])
    run(input_module, config_dict, expected_results,9)

def test_vectors_idd_configuration_cert_3_time(log_level=logging.INFO):
    config_dict = {
        'console_log_level': log_level,
        'logs_path': LOGS_PATH,
        'scenario_path': Path(__file__).parent / 'icd_test_vectors/configuration_1/16_AUG_2023_GST_05_00_01_fixed.csv',
        'exec_path': Path(__file__).parent / 'idd_test_vectors/',
        'download_pki': False,
        'download_merkle': False,
        'download_sca': False,
        'download_rca': False,
        'CERT_FOLDER' : Path(__file__).parent / 'idd_test_vectors/',
        'USER_IDD_CERT' : {
            "CERT_PKIEE" : "Cert 4 - PKI/pki.crt",
            "CERT_MERKLE" : "Cert 4 - MK/mk.crt",
            "CERT_ICA" : "Cert 3- ICA/ica_time.crt",
            "CERT_SCA" : "Cert 2 - SCA/sca.crt",
            "CERT_RCA" : "Cert 1 - RCA/rca.crt"
        },

        'USER_IDD_CRL' : {
            "CRL_ICA" : 'CRL 3 - ICA/ica.crl',
            "CRL_SCA" : 'CRL 2 - SCA/sca.crl',
            "CRL_RCA" : 'CRL 1 - RCA/rca.crl'
        },
        "MERKLE_NAME" : Path(__file__).parent / "idd_test_vectors/Cert/OSNMA_MerkleTree_20240115100000_newPKID_1.xml"
    }

    expected_results = {
        "warnings": 1,
        "errors": 0
    }

    input_module = ICDTestVectors(config_dict['scenario_path'])
    run(input_module, config_dict, expected_results,10)

def test_vectors_idd_configuration_cert_3_issuer(log_level=logging.INFO):
    config_dict = {
        'console_log_level': log_level,
        'logs_path': LOGS_PATH,
        'scenario_path': Path(__file__).parent / 'icd_test_vectors/configuration_1/16_AUG_2023_GST_05_00_01_fixed.csv',
        'exec_path': Path(__file__).parent / 'idd_test_vectors/',
        'download_pki': False,
        'download_merkle': False,
        'download_sca': False,
        'download_rca': False,
        'CERT_FOLDER' : Path(__file__).parent / 'idd_test_vectors/',
        'USER_IDD_CERT' : {
            "CERT_PKIEE" : "Cert 4 - PKI/pki.crt",
            "CERT_MERKLE" : "Cert 4 - MK/mk.crt",
            "CERT_ICA" : "Cert 3- ICA/ica_issuer.crt",
            "CERT_SCA" : "Cert 2 - SCA/sca.crt",
            "CERT_RCA" : "Cert 1 - RCA/rca.crt"
        },

        'USER_IDD_CRL' : {
            "CRL_ICA" : 'CRL 3 - ICA/ica.crl',
            "CRL_SCA" : 'CRL 2 - SCA/sca.crl',
            "CRL_RCA" : 'CRL 1 - RCA/rca.crl'
        },
        "MERKLE_NAME" : Path(__file__).parent / "idd_test_vectors/Cert/OSNMA_MerkleTree_20240115100000_newPKID_1.xml"
    }

    expected_results = {
        "warnings": 1,
        "errors": 0
    }

    input_module = ICDTestVectors(config_dict['scenario_path'])
    run(input_module, config_dict, expected_results,11)

def test_vectors_idd_configuration_cert_3_signature(log_level=logging.INFO):
    config_dict = {
        'console_log_level': log_level,
        'logs_path': LOGS_PATH,
        'scenario_path': Path(__file__).parent / 'icd_test_vectors/configuration_1/16_AUG_2023_GST_05_00_01_fixed.csv',
        'exec_path': Path(__file__).parent / 'idd_test_vectors/',
        'download_pki': False,
        'download_merkle': False,
        'download_sca': False,
        'download_rca': False,
        'CERT_FOLDER' : Path(__file__).parent / 'idd_test_vectors/',
        'USER_IDD_CERT' : {
            "CERT_PKIEE" : "Cert 4 - PKI/pki.crt",
            "CERT_MERKLE" : "Cert 4 - MK/mk.crt",
            "CERT_ICA" : "Cert 3- ICA/ica_signature.crt",
            "CERT_SCA" : "Cert 2 - SCA/sca.crt",
            "CERT_RCA" : "Cert 1 - RCA/rca.crt"
        },

        'USER_IDD_CRL' : {
            "CRL_ICA" : 'CRL 3 - ICA/ica.crl',
            "CRL_SCA" : 'CRL 2 - SCA/sca.crl',
            "CRL_RCA" : 'CRL 1 - RCA/rca.crl'
        },
        "MERKLE_NAME" : Path(__file__).parent / "idd_test_vectors/Cert/OSNMA_MerkleTree_20240115100000_newPKID_1.xml"
    }

    expected_results = {
        "warnings": 1,
        "errors": 0
    }

    input_module = ICDTestVectors(config_dict['scenario_path'])
    run(input_module, config_dict, expected_results,12)

def test_vectors_idd_configuration_cert_3_revokated(log_level=logging.INFO):
    config_dict = {
        'console_log_level': log_level,
        'logs_path': LOGS_PATH,
        'scenario_path': Path(__file__).parent / 'icd_test_vectors/configuration_1/16_AUG_2023_GST_05_00_01_fixed.csv',
        'exec_path': Path(__file__).parent / 'idd_test_vectors/',
        'download_pki': False,
        'download_merkle': False,
        'download_sca': False,
        'download_rca': False,
        'CERT_FOLDER' : Path(__file__).parent / 'idd_test_vectors/',
        'USER_IDD_CERT' : {
            "CERT_PKIEE" : "Cert 4 - PKI/pki.crt",
            "CERT_MERKLE" : "Cert 4 - MK/mk.crt",
            "CERT_ICA" : "Cert 3- ICA/ica.crt",
            "CERT_SCA" : "Cert 2 - SCA/sca.crt",
            "CERT_RCA" : "Cert 1 - RCA/rca.crt"
        },

        'USER_IDD_CRL' : {
            "CRL_ICA" : 'CRL 3 - ICA/ica.crl',
            "CRL_SCA" : 'CRL 2 - SCA/sca_revokated.crl',
            "CRL_RCA" : 'CRL 1 - RCA/rca.crl'
        },
        "MERKLE_NAME" : Path(__file__).parent / "idd_test_vectors/Cert/OSNMA_MerkleTree_20240115100000_newPKID_1.xml"
    }

    expected_results = {
        "warnings": 1,
        "errors": 0
    }

    input_module = ICDTestVectors(config_dict['scenario_path'])
    run(input_module, config_dict, expected_results,13)

def test_vectors_idd_configuration_cert_4_MK_time(log_level=logging.INFO):
    config_dict = {
        'console_log_level': log_level,
        'logs_path': LOGS_PATH,
        'scenario_path': Path(__file__).parent / 'icd_test_vectors/configuration_1/16_AUG_2023_GST_05_00_01_fixed.csv',
        'exec_path': Path(__file__).parent / 'idd_test_vectors/',
        'download_pki': False,
        'download_merkle': False,
        'download_sca': False,
        'download_rca': False,
        'CERT_FOLDER' : Path(__file__).parent / 'idd_test_vectors/',
        'USER_IDD_CERT' : {
            "CERT_PKIEE" : "Cert 4 - PKI/pki.crt",
            "CERT_MERKLE" : "Cert 4 - MK/mk_time.crt",
            "CERT_ICA" : "Cert 3- ICA/ica.crt",
            "CERT_SCA" : "Cert 2 - SCA/sca.crt",
            "CERT_RCA" : "Cert 1 - RCA/rca.crt"
        },

        'USER_IDD_CRL' : {
            "CRL_ICA" : 'CRL 3 - ICA/ica.crl',
            "CRL_SCA" : 'CRL 2 - SCA/sca.crl',
            "CRL_RCA" : 'CRL 1 - RCA/rca.crl'
        },
        "MERKLE_NAME" : Path(__file__).parent / "idd_test_vectors/Cert/OSNMA_MerkleTree_20240115100000_newPKID_1.xml"
    }

    expected_results = {
        "warnings": 1,
        "errors": 0
    }

    input_module = ICDTestVectors(config_dict['scenario_path'])
    run(input_module, config_dict, expected_results,14)

def test_vectors_idd_configuration_cert_4_MK_issuer(log_level=logging.INFO):
    config_dict = {
        'console_log_level': log_level,
        'logs_path': LOGS_PATH,
        'scenario_path': Path(__file__).parent / 'icd_test_vectors/configuration_1/16_AUG_2023_GST_05_00_01_fixed.csv',
        'exec_path': Path(__file__).parent / 'idd_test_vectors/',
        'download_pki': False,
        'download_merkle': False,
        'download_sca': False,
        'download_rca': False,
        'CERT_FOLDER' : Path(__file__).parent / 'idd_test_vectors/',
        'USER_IDD_CERT' : {
            "CERT_PKIEE" : "Cert 4 - PKI/pki.crt",
            "CERT_MERKLE" : "Cert 4 - MK/mk_issuer.crt",
            "CERT_ICA" : "Cert 3- ICA/ica.crt",
            "CERT_SCA" : "Cert 2 - SCA/sca.crt",
            "CERT_RCA" : "Cert 1 - RCA/rca.crt"
        },

        'USER_IDD_CRL' : {
            "CRL_ICA" : 'CRL 3 - ICA/ica.crl',
            "CRL_SCA" : 'CRL 2 - SCA/sca.crl',
            "CRL_RCA" : 'CRL 1 - RCA/rca.crl'
        },
        "MERKLE_NAME" : Path(__file__).parent / "idd_test_vectors/Cert/OSNMA_MerkleTree_20240115100000_newPKID_1.xml"
    }

    expected_results = {
        "warnings": 1,
        "errors": 0
    }

    input_module = ICDTestVectors(config_dict['scenario_path'])
    run(input_module, config_dict, expected_results,15)

def test_vectors_idd_configuration_cert_4_MK_signature(log_level=logging.INFO):
    config_dict = {
        'console_log_level': log_level,
        'logs_path': LOGS_PATH,
        'scenario_path': Path(__file__).parent / 'icd_test_vectors/configuration_1/16_AUG_2023_GST_05_00_01_fixed.csv',
        'exec_path': Path(__file__).parent / 'idd_test_vectors/',
        'download_pki': False,
        'download_merkle': False,
        'download_sca': False,
        'download_rca': False,
        'CERT_FOLDER' : Path(__file__).parent / 'idd_test_vectors/',
        'USER_IDD_CERT' : {
            "CERT_PKIEE" : "Cert 4 - PKI/pki.crt",
            "CERT_MERKLE" : "Cert 4 - MK/mk_signature.crt",
            "CERT_ICA" : "Cert 3- ICA/ica.crt",
            "CERT_SCA" : "Cert 2 - SCA/sca.crt",
            "CERT_RCA" : "Cert 1 - RCA/rca.crt"
        },

        'USER_IDD_CRL' : {
            "CRL_ICA" : 'CRL 3 - ICA/ica.crl',
            "CRL_SCA" : 'CRL 2 - SCA/sca.crl',
            "CRL_RCA" : 'CRL 1 - RCA/rca.crl'
        },
        "MERKLE_NAME" : Path(__file__).parent / "idd_test_vectors/Cert/OSNMA_MerkleTree_20240115100000_newPKID_1.xml"
    }

    expected_results = {
        "warnings": 1,
        "errors": 0
    }

    input_module = ICDTestVectors(config_dict['scenario_path'])
    run(input_module, config_dict, expected_results,16)

def test_vectors_idd_configuration_cert_4_MK_revokated(log_level=logging.INFO):
    config_dict = {
        'console_log_level': log_level,
        'logs_path': LOGS_PATH,
        'scenario_path': Path(__file__).parent / 'icd_test_vectors/configuration_1/16_AUG_2023_GST_05_00_01_fixed.csv',
        'exec_path': Path(__file__).parent / 'idd_test_vectors/',
        'download_pki': False,
        'download_merkle': False,
        'download_sca': False,
        'download_rca': False,
        'CERT_FOLDER' : Path(__file__).parent / 'idd_test_vectors/',
        'USER_IDD_CERT' : {
            "CERT_PKIEE" : "Cert 4 - PKI/pki.crt",
            "CERT_MERKLE" : "Cert 4 - MK/mk.crt",
            "CERT_ICA" : "Cert 3- ICA/ica.crt",
            "CERT_SCA" : "Cert 2 - SCA/sca.crt",
            "CERT_RCA" : "Cert 1 - RCA/rca.crt"
        },

        'USER_IDD_CRL' : {
            "CRL_ICA" : 'CRL 3 - ICA/ica_revokatedMK.crl',
            "CRL_SCA" : 'CRL 2 - SCA/sca.crl',
            "CRL_RCA" : 'CRL 1 - RCA/rca.crl'
        },
        "MERKLE_NAME" : Path(__file__).parent / "idd_test_vectors/Cert/OSNMA_MerkleTree_20240115100000_newPKID_1.xml"
    }

    expected_results = {
        "warnings": 1,
        "errors": 0
    }

    input_module = ICDTestVectors(config_dict['scenario_path'])
    run(input_module, config_dict, expected_results,17)

def test_vectors_idd_configuration_cert_4_PKI_time(log_level=logging.INFO):
    config_dict = {
        'console_log_level': log_level,
        'logs_path': LOGS_PATH,
        'scenario_path': Path(__file__).parent / 'icd_test_vectors/configuration_1/16_AUG_2023_GST_05_00_01_fixed.csv',
        'exec_path': Path(__file__).parent / 'idd_test_vectors/',
        'download_pki': False,
        'download_merkle': False,
        'download_sca': False,
        'download_rca': False,
        'CERT_FOLDER' : Path(__file__).parent / 'idd_test_vectors/',
        'USER_IDD_CERT' : {
            "CERT_PKIEE" : "Cert 4 - PKI/pki_time.crt",
            "CERT_MERKLE" : "Cert 4 - MK/mk.crt",
            "CERT_ICA" : "Cert 3- ICA/ica.crt",
            "CERT_SCA" : "Cert 2 - SCA/sca.crt",
            "CERT_RCA" : "Cert 1 - RCA/rca.crt"
        },

        'USER_IDD_CRL' : {
            "CRL_ICA" : 'CRL 3 - ICA/ica.crl',
            "CRL_SCA" : 'CRL 2 - SCA/sca.crl',
            "CRL_RCA" : 'CRL 1 - RCA/rca.crl'
        },
        "MERKLE_NAME" : Path(__file__).parent / "idd_test_vectors/Cert/OSNMA_MerkleTree_20240115100000_newPKID_1.xml"
    }

    expected_results = {
        "warnings": 1,
        "errors": 0
    }

    input_module = ICDTestVectors(config_dict['scenario_path'])
    run(input_module, config_dict, expected_results,18)

def test_vectors_idd_configuration_cert_4_PKI_issuer(log_level=logging.INFO):
    config_dict = {
        'console_log_level': log_level,
        'logs_path': LOGS_PATH,
        'scenario_path': Path(__file__).parent / 'icd_test_vectors/configuration_1/16_AUG_2023_GST_05_00_01_fixed.csv',
        'exec_path': Path(__file__).parent / 'idd_test_vectors/',
        'download_pki': False,
        'download_merkle': False,
        'download_sca': False,
        'download_rca': False,
        'CERT_FOLDER' : Path(__file__).parent / 'idd_test_vectors/',
        'USER_IDD_CERT' : {
            "CERT_PKIEE" : "Cert 4 - PKI/pki_issuer.crt",
            "CERT_MERKLE" : "Cert 4 - MK/mk.crt",
            "CERT_ICA" : "Cert 3- ICA/ica.crt",
            "CERT_SCA" : "Cert 2 - SCA/sca.crt",
            "CERT_RCA" : "Cert 1 - RCA/rca.crt"
        },

        'USER_IDD_CRL' : {
            "CRL_ICA" : 'CRL 3 - ICA/ica.crl',
            "CRL_SCA" : 'CRL 2 - SCA/sca.crl',
            "CRL_RCA" : 'CRL 1 - RCA/rca.crl'
        },
        "MERKLE_NAME" : Path(__file__).parent / "idd_test_vectors/Cert/OSNMA_MerkleTree_20240115100000_newPKID_1.xml"
    }

    expected_results = {
        "warnings": 1,
        "errors": 0
    }

    input_module = ICDTestVectors(config_dict['scenario_path'])
    run(input_module, config_dict, expected_results,19)

def test_vectors_idd_configuration_cert_4_PKI_signature(log_level=logging.INFO):
    config_dict = {
        'console_log_level': log_level,
        'logs_path': LOGS_PATH,
        'scenario_path': Path(__file__).parent / 'icd_test_vectors/configuration_1/16_AUG_2023_GST_05_00_01_fixed.csv',
        'exec_path': Path(__file__).parent / 'idd_test_vectors/',
        'download_pki': False,
        'download_merkle': False,
        'download_sca': False,
        'download_rca': False,
        'CERT_FOLDER' : Path(__file__).parent / 'idd_test_vectors/',
        'USER_IDD_CERT' : {
            "CERT_PKIEE" : "Cert 4 - PKI/pki_signature.crt",
            "CERT_MERKLE" : "Cert 4 - MK/mk.crt",
            "CERT_ICA" : "Cert 3- ICA/ica.crt",
            "CERT_SCA" : "Cert 2 - SCA/sca.crt",
            "CERT_RCA" : "Cert 1 - RCA/rca.crt"
        },

        'USER_IDD_CRL' : {
            "CRL_ICA" : 'CRL 3 - ICA/ica.crl',
            "CRL_SCA" : 'CRL 2 - SCA/sca.crl',
            "CRL_RCA" : 'CRL 1 - RCA/rca.crl'
        },
        "MERKLE_NAME" : Path(__file__).parent / "idd_test_vectors/Cert/OSNMA_MerkleTree_20240115100000_newPKID_1.xml"
    }

    expected_results = {
        "warnings": 1,
        "errors": 0
    }

    input_module = ICDTestVectors(config_dict['scenario_path'])
    run(input_module, config_dict, expected_results,20)

def test_vectors_idd_configuration_cert_4_PKI_revokated(log_level=logging.INFO):
    config_dict = {
        'console_log_level': log_level,
        'logs_path': LOGS_PATH,
        'scenario_path': Path(__file__).parent / 'icd_test_vectors/configuration_1/16_AUG_2023_GST_05_00_01_fixed.csv',
        'exec_path': Path(__file__).parent / 'idd_test_vectors/',
        'download_pki': False,
        'download_merkle': False,
        'download_sca': False,
        'download_rca': False,
        'CERT_FOLDER' : Path(__file__).parent / 'idd_test_vectors/',
        'USER_IDD_CERT' : {
            "CERT_PKIEE" : "Cert 4 - PKI/pki.crt",
            "CERT_MERKLE" : "Cert 4 - MK/mk.crt",
            "CERT_ICA" : "Cert 3- ICA/ica.crt",
            "CERT_SCA" : "Cert 2 - SCA/sca.crt",
            "CERT_RCA" : "Cert 1 - RCA/rca.crt"
        },

        'USER_IDD_CRL' : {
            "CRL_ICA" : 'CRL 3 - ICA/ica_revokatedPKI.crl',
            "CRL_SCA" : 'CRL 2 - SCA/sca.crl',
            "CRL_RCA" : 'CRL 1 - RCA/rca.crl'
        },
        "MERKLE_NAME" : Path(__file__).parent / "idd_test_vectors/Cert/OSNMA_MerkleTree_20240115100000_newPKID_1.xml"
    }

    expected_results = {
        "warnings": 1,
        "errors": 0
    }

    input_module = ICDTestVectors(config_dict['scenario_path'])
    run(input_module, config_dict, expected_results,21)

def test_vectors_idd_configuration_crl_1_time(log_level=logging.INFO):
    config_dict = {
        'console_log_level': log_level,
        'logs_path': LOGS_PATH,
        'scenario_path': Path(__file__).parent / 'icd_test_vectors/configuration_1/16_AUG_2023_GST_05_00_01_fixed.csv',
        'exec_path': Path(__file__).parent / 'idd_test_vectors/',
        'download_pki': False,
        'download_merkle': False,
        'download_sca': False,
        'download_rca': False,
        'CERT_FOLDER' : Path(__file__).parent / 'idd_test_vectors/',
        'USER_IDD_CERT' : {
            "CERT_PKIEE" : "Cert 4 - PKI/pki.crt",
            "CERT_MERKLE" : "Cert 4 - MK/mk.crt",
            "CERT_ICA" : "Cert 3- ICA/ica.crt",
            "CERT_SCA" : "Cert 2 - SCA/sca.crt",
            "CERT_RCA" : "Cert 1 - RCA/rca.crt"
        },

        'USER_IDD_CRL' : {
            "CRL_ICA" : 'CRL 3 - ICA/ica.crl',
            "CRL_SCA" : 'CRL 2 - SCA/sca.crl',
            "CRL_RCA" : 'CRL 1 - RCA/rca_time.crl'
        },
        "MERKLE_NAME" : Path(__file__).parent / "idd_test_vectors/Cert/OSNMA_MerkleTree_20240115100000_newPKID_1.xml"
    }

    expected_results = {
        "warnings": 1,
        "errors": 0
    }

    input_module = ICDTestVectors(config_dict['scenario_path'])
    run(input_module, config_dict, expected_results,22)

def test_vectors_idd_configuration_crl_1_issuer(log_level=logging.INFO):
    config_dict = {
        'console_log_level': log_level,
        'logs_path': LOGS_PATH,
        'scenario_path': Path(__file__).parent / 'icd_test_vectors/configuration_1/16_AUG_2023_GST_05_00_01_fixed.csv',
        'exec_path': Path(__file__).parent / 'idd_test_vectors/',
        'download_pki': False,
        'download_merkle': False,
        'download_sca': False,
        'download_rca': False,
        'CERT_FOLDER' : Path(__file__).parent / 'idd_test_vectors/',
        'USER_IDD_CERT' : {
            "CERT_PKIEE" : "Cert 4 - PKI/pki.crt",
            "CERT_MERKLE" : "Cert 4 - MK/mk.crt",
            "CERT_ICA" : "Cert 3- ICA/ica.crt",
            "CERT_SCA" : "Cert 2 - SCA/sca.crt",
            "CERT_RCA" : "Cert 1 - RCA/rca.crt"
        },

        'USER_IDD_CRL' : {
            "CRL_ICA" : 'CRL 3 - ICA/ica.crl',
            "CRL_SCA" : 'CRL 2 - SCA/sca.crl',
            "CRL_RCA" : 'CRL 1 - RCA/rca_issuer.crl'
        },
        "MERKLE_NAME" : Path(__file__).parent / "idd_test_vectors/Cert/OSNMA_MerkleTree_20240115100000_newPKID_1.xml"
    }

    expected_results = {
        "warnings": 1,
        "errors": 0
    }

    input_module = ICDTestVectors(config_dict['scenario_path'])
    run(input_module, config_dict, expected_results,23)

def test_vectors_idd_configuration_crl_1_signature(log_level=logging.INFO):
    config_dict = {
        'console_log_level': log_level,
        'logs_path': LOGS_PATH,
        'scenario_path': Path(__file__).parent / 'icd_test_vectors/configuration_1/16_AUG_2023_GST_05_00_01_fixed.csv',
        'exec_path': Path(__file__).parent / 'idd_test_vectors/',
        'download_pki': False,
        'download_merkle': False,
        'download_sca': False,
        'download_rca': False,
        'CERT_FOLDER' : Path(__file__).parent / 'idd_test_vectors/',
        'USER_IDD_CERT' : {
            "CERT_PKIEE" : "Cert 4 - PKI/pki.crt",
            "CERT_MERKLE" : "Cert 4 - MK/mk.crt",
            "CERT_ICA" : "Cert 3- ICA/ica.crt",
            "CERT_SCA" : "Cert 2 - SCA/sca.crt",
            "CERT_RCA" : "Cert 1 - RCA/rca.crt"
        },

        'USER_IDD_CRL' : {
            "CRL_ICA" : 'CRL 3 - ICA/ica.crl',
            "CRL_SCA" : 'CRL 2 - SCA/sca.crl',
            "CRL_RCA" : 'CRL 1 - RCA/rca_signature.crl'
        },
        "MERKLE_NAME" : Path(__file__).parent / "idd_test_vectors/Cert/OSNMA_MerkleTree_20240115100000_newPKID_1.xml"
    }

    expected_results = {
        "warnings": 1,
        "errors": 0
    }

    input_module = ICDTestVectors(config_dict['scenario_path'])
    run(input_module, config_dict, expected_results,24)

def test_vectors_idd_configuration_crl_2_time(log_level=logging.INFO):
    config_dict = {
        'console_log_level': log_level,
        'logs_path': LOGS_PATH,
        'scenario_path': Path(__file__).parent / 'icd_test_vectors/configuration_1/16_AUG_2023_GST_05_00_01_fixed.csv',
        'exec_path': Path(__file__).parent / 'idd_test_vectors/',
        'download_pki': False,
        'download_merkle': False,
        'download_sca': False,
        'download_rca': False,
        'CERT_FOLDER' : Path(__file__).parent / 'idd_test_vectors/',
        'USER_IDD_CERT' : {
            "CERT_PKIEE" : "Cert 4 - PKI/pki.crt",
            "CERT_MERKLE" : "Cert 4 - MK/mk.crt",
            "CERT_ICA" : "Cert 3- ICA/ica.crt",
            "CERT_SCA" : "Cert 2 - SCA/sca.crt",
            "CERT_RCA" : "Cert 1 - RCA/rca.crt"
        },

        'USER_IDD_CRL' : {
            "CRL_ICA" : 'CRL 3 - ICA/ica.crl',
            "CRL_SCA" : 'CRL 2 - SCA/sca_time.crl',
            "CRL_RCA" : 'CRL 1 - RCA/rca.crl'
        },
        "MERKLE_NAME" : Path(__file__).parent / "idd_test_vectors/Cert/OSNMA_MerkleTree_20240115100000_newPKID_1.xml"
    }

    expected_results = {
        "warnings": 1,
        "errors": 0
    }

    input_module = ICDTestVectors(config_dict['scenario_path'])
    run(input_module, config_dict, expected_results,25)

def test_vectors_idd_configuration_crl_2_issuer(log_level=logging.INFO):
    config_dict = {
        'console_log_level': log_level,
        'logs_path': LOGS_PATH,
        'scenario_path': Path(__file__).parent / 'icd_test_vectors/configuration_1/16_AUG_2023_GST_05_00_01_fixed.csv',
        'exec_path': Path(__file__).parent / 'idd_test_vectors/',
        'download_pki': False,
        'download_merkle': False,
        'download_sca': False,
        'download_rca': False,
        'CERT_FOLDER' : Path(__file__).parent / 'idd_test_vectors/',
        'USER_IDD_CERT' : {
            "CERT_PKIEE" : "Cert 4 - PKI/pki.crt",
            "CERT_MERKLE" : "Cert 4 - MK/mk.crt",
            "CERT_ICA" : "Cert 3- ICA/ica.crt",
            "CERT_SCA" : "Cert 2 - SCA/sca.crt",
            "CERT_RCA" : "Cert 1 - RCA/rca.crt"
        },

        'USER_IDD_CRL' : {
            "CRL_ICA" : 'CRL 3 - ICA/ica.crl',
            "CRL_SCA" : 'CRL 2 - SCA/sca_issuer.crl',
            "CRL_RCA" : 'CRL 1 - RCA/rca.crl'
        },
        "MERKLE_NAME" : Path(__file__).parent / "idd_test_vectors/Cert/OSNMA_MerkleTree_20240115100000_newPKID_1.xml"
    }

    expected_results = {
        "warnings": 1,
        "errors": 0
    }

    input_module = ICDTestVectors(config_dict['scenario_path'])
    run(input_module, config_dict, expected_results,26)

def test_vectors_idd_configuration_crl_2_signature(log_level=logging.INFO):
    config_dict = {
        'console_log_level': log_level,
        'logs_path': LOGS_PATH,
        'scenario_path': Path(__file__).parent / 'icd_test_vectors/configuration_1/16_AUG_2023_GST_05_00_01_fixed.csv',
        'exec_path': Path(__file__).parent / 'idd_test_vectors/',
        'download_pki': False,
        'download_merkle': False,
        'download_sca': False,
        'download_rca': False,
        'CERT_FOLDER' : Path(__file__).parent / 'idd_test_vectors/',
        'USER_IDD_CERT' : {
            "CERT_PKIEE" : "Cert 4 - PKI/pki.crt",
            "CERT_MERKLE" : "Cert 4 - MK/mk.crt",
            "CERT_ICA" : "Cert 3- ICA/ica.crt",
            "CERT_SCA" : "Cert 2 - SCA/sca.crt",
            "CERT_RCA" : "Cert 1 - RCA/rca.crt"
        },

        'USER_IDD_CRL' : {
            "CRL_ICA" : 'CRL 3 - ICA/ica.crl',
            "CRL_SCA" : 'CRL 2 - SCA/sca_signature.crl',
            "CRL_RCA" : 'CRL 1 - RCA/rca.crl'
        },
        "MERKLE_NAME" : Path(__file__).parent / "idd_test_vectors/Cert/OSNMA_MerkleTree_20240115100000_newPKID_1.xml"
    }

    expected_results = {
        "warnings": 1,
        "errors": 0
    }

    input_module = ICDTestVectors(config_dict['scenario_path'])
    run(input_module, config_dict, expected_results,27)

def test_vectors_idd_configuration_crl_3_time(log_level=logging.INFO):
    config_dict = {
        'console_log_level': log_level,
        'logs_path': LOGS_PATH,
        'scenario_path': Path(__file__).parent / 'icd_test_vectors/configuration_1/16_AUG_2023_GST_05_00_01_fixed.csv',
        'exec_path': Path(__file__).parent / 'idd_test_vectors/',
        'download_pki': False,
        'download_merkle': False,
        'download_sca': False,
        'download_rca': False,
        'CERT_FOLDER' : Path(__file__).parent / 'idd_test_vectors/',
        'USER_IDD_CERT' : {
            "CERT_PKIEE" : "Cert 4 - PKI/pki.crt",
            "CERT_MERKLE" : "Cert 4 - MK/mk.crt",
            "CERT_ICA" : "Cert 3- ICA/ica.crt",
            "CERT_SCA" : "Cert 2 - SCA/sca.crt",
            "CERT_RCA" : "Cert 1 - RCA/rca.crt"
        },

        'USER_IDD_CRL' : {
            "CRL_ICA" : 'CRL 3 - ICA/ica_time.crl',
            "CRL_SCA" : 'CRL 2 - SCA/sca.crl',
            "CRL_RCA" : 'CRL 1 - RCA/rca.crl'
        },
        "MERKLE_NAME" : Path(__file__).parent / "idd_test_vectors/Cert/OSNMA_MerkleTree_20240115100000_newPKID_1.xml"
    }

    expected_results = {
        "warnings": 1,
        "errors": 0
    }

    input_module = ICDTestVectors(config_dict['scenario_path'])
    run(input_module, config_dict, expected_results,28)

def test_vectors_idd_configuration_crl_3_issuer(log_level=logging.INFO):
    config_dict = {
        'console_log_level': log_level,
        'logs_path': LOGS_PATH,
        'scenario_path': Path(__file__).parent / 'icd_test_vectors/configuration_1/16_AUG_2023_GST_05_00_01_fixed.csv',
        'exec_path': Path(__file__).parent / 'idd_test_vectors/',
        'download_pki': False,
        'download_merkle': False,
        'download_sca': False,
        'download_rca': False,
        'CERT_FOLDER' : Path(__file__).parent / 'idd_test_vectors/',
        'USER_IDD_CERT' : {
            "CERT_PKIEE" : "Cert 4 - PKI/pki.crt",
            "CERT_MERKLE" : "Cert 4 - MK/mk.crt",
            "CERT_ICA" : "Cert 3- ICA/ica.crt",
            "CERT_SCA" : "Cert 2 - SCA/sca.crt",
            "CERT_RCA" : "Cert 1 - RCA/rca.crt"
        },

        'USER_IDD_CRL' : {
            "CRL_ICA" : 'CRL 3 - ICA/ica_issuer.crl',
            "CRL_SCA" : 'CRL 2 - SCA/sca.crl',
            "CRL_RCA" : 'CRL 1 - RCA/rca.crl'
        },
        "MERKLE_NAME" : Path(__file__).parent / "idd_test_vectors/Cert/OSNMA_MerkleTree_20240115100000_newPKID_1.xml"
    }

    expected_results = {
        "warnings": 1,
        "errors": 0
    }

    input_module = ICDTestVectors(config_dict['scenario_path'])
    run(input_module, config_dict, expected_results,29)

def test_vectors_idd_configuration_crl_3_signature(log_level=logging.INFO):
    config_dict = {
        'console_log_level': log_level,
        'logs_path': LOGS_PATH,
        'scenario_path': Path(__file__).parent / 'icd_test_vectors/configuration_1/16_AUG_2023_GST_05_00_01_fixed.csv',
        'exec_path': Path(__file__).parent / 'idd_test_vectors/',
        'download_pki': False,
        'download_merkle': False,
        'download_sca': False,
        'download_rca': False,
        'CERT_FOLDER' : Path(__file__).parent / 'idd_test_vectors/',
        'USER_IDD_CERT' : {
            "CERT_PKIEE" : "Cert 4 - PKI/pki.crt",
            "CERT_MERKLE" : "Cert 4 - MK/mk.crt",
            "CERT_ICA" : "Cert 3- ICA/ica.crt",
            "CERT_SCA" : "Cert 2 - SCA/sca.crt",
            "CERT_RCA" : "Cert 1 - RCA/rca.crt"
        },

        'USER_IDD_CRL' : {
            "CRL_ICA" : 'CRL 3 - ICA/ica.crl',
            "CRL_SCA" : 'CRL 2 - SCA/sca.crl',
            "CRL_RCA" : 'CRL 1 - RCA/rca_signature.crl'
        },
        "MERKLE_NAME" : Path(__file__).parent / "idd_test_vectors/Cert/OSNMA_MerkleTree_20240115100000_newPKID_1.xml"
    }

    expected_results = {
        "warnings": 1,
        "errors": 0
    }

    input_module = ICDTestVectors(config_dict['scenario_path'])
    run(input_module, config_dict, expected_results,30)



if __name__ == "__main__":

    general_log_level = logging.CRITICAL
    test_passed = 0
    test_done = 0

    print(f"\nDownlaod all Cert and CRL")
    try:
        test_vectors_idd_configuration(general_log_level)
    except AssertionError:
        print(f"\tFAILED")
    else:
        test_passed += 1
        print(f"\tCORRECT")
    finally:
        test_done += 1

    print(f"\nAll Cert and CRL Good")
    try:
        test_vectors_idd_configuration_Good(general_log_level)
    except AssertionError:
        print(f"\tFAILED")
    else:
        test_passed += 1
        print(f"\tCORRECT")
    finally:
        test_done += 1

    #------------------------------------------------------------------------------------

    print(f"\nCert RCA Time Fail")
    try:
        test_vectors_idd_configuration_cert_1_time(general_log_level)
    except AssertionError:
        print(f"\tFAILED")
    else:
        test_passed += 1
        print(f"\tCORRECT")
    finally:
        test_done += 1
    
    print(f"\nCert RCA Issuer Fail")
    try:
        test_vectors_idd_configuration_cert_1_issuer(general_log_level)
    except AssertionError:
        print(f"\tFAILED")
    else:
        test_passed += 1
        print(f"\tCORRECT")
    finally:
        test_done += 1

    print(f"\nCert RCA Signature Fail")
    try:
        test_vectors_idd_configuration_cert_1_signature(general_log_level)
    except AssertionError:
        print(f"\tFAILED")
    else:
        test_passed += 1
        print(f"\tCORRECT")
    finally:
        test_done += 1

    #------------------------------------------------------------------------------------

    print(f"\nCert SCA Time Fail")
    try:
        test_vectors_idd_configuration_cert_2_time(general_log_level)
    except AssertionError:
        print(f"\tFAILED")
    else:
        test_passed += 1
        print(f"\tCORRECT")
    finally:
        test_done += 1
    
    print(f"\nCert SCA Issuer Fail")
    try:
        test_vectors_idd_configuration_cert_2_issuer(general_log_level)
    except AssertionError:
        print(f"\tFAILED")
    else:
        test_passed += 1
        print(f"\tCORRECT")
    finally:
        test_done += 1
    
    print(f"\nCert SCA Signature Fail")
    try:
        test_vectors_idd_configuration_cert_2_signature(general_log_level)
    except AssertionError:
        print(f"\tFAILED")
    else:
        test_passed += 1
        print(f"\tCORRECT")
    finally:
        test_done += 1

    print(f"\nCert SCA Revokated Fail")
    try:
        test_vectors_idd_configuration_cert_2_revokated(general_log_level)
    except AssertionError:
        print(f"\tFAILED")
    else:
        test_passed += 1
        print(f"\tCORRECT")
    finally:
        test_done += 1
    
    #------------------------------------------------------------------------------------

        print(f"\nCert ICA Time Fail")
    try:
        test_vectors_idd_configuration_cert_3_time(general_log_level)
    except AssertionError:
        print(f"\tFAILED")
    else:
        test_passed += 1
        print(f"\tCORRECT")
    finally:
        test_done += 1
    
    print(f"\nCert ICA Issuer Fail")
    try:
        test_vectors_idd_configuration_cert_3_issuer(general_log_level)
    except AssertionError:
        print(f"\tFAILED")
    else:
        test_passed += 1
        print(f"\tCORRECT")
    finally:
        test_done += 1
    
    print(f"\nCert ICA Signature Fail")
    try:
        test_vectors_idd_configuration_cert_3_signature(general_log_level)
    except AssertionError:
        print(f"\tFAILED")
    else:
        test_passed += 1
        print(f"\tCORRECT")
    finally:
        test_done += 1
    
    print(f"\nCert ICA Revokated Fail")
    try:
        test_vectors_idd_configuration_cert_3_revokated(general_log_level)
    except AssertionError:
        print(f"\tFAILED")
    else:
        test_passed += 1
        print(f"\tCORRECT")
    finally:
        test_done += 1
    
    #------------------------------------------------------------------------------------

        print(f"\nCert MK EE Time Fail")
    try:
        test_vectors_idd_configuration_cert_4_MK_time(general_log_level)
    except AssertionError:
        print(f"\tFAILED")
    else:
        test_passed += 1
        print(f"\tCORRECT")
    finally:
        test_done += 1
    
    print(f"\nCert MK EE Time Fail")
    try:
        test_vectors_idd_configuration_cert_4_MK_issuer(general_log_level)
    except AssertionError:
        print(f"\tFAILED")
    else:
        test_passed += 1
        print(f"\tCORRECT")
    finally:
        test_done += 1
    
    print(f"\nCert MK EE Signature Fail")
    try:
        test_vectors_idd_configuration_cert_4_MK_signature(general_log_level)
    except AssertionError:
        print(f"\tFAILED")
    else:
        test_passed += 1
        print(f"\tCORRECT")
    finally:
        test_done += 1
    
    print(f"\nCert MK EE Revokated Fail")
    try:
        test_vectors_idd_configuration_cert_4_MK_revokated(general_log_level)
    except AssertionError:
        print(f"\tFAILED")
    else:
        test_passed += 1
        print(f"\tCORRECT")
    finally:
        test_done += 1

    #------------------------------------------------------------------------------------

        print(f"\nCert PKI Time Fail")
    try:
        test_vectors_idd_configuration_cert_4_PKI_time(general_log_level)
    except AssertionError:
        print(f"\tFAILED")
    else:
        test_passed += 1
        print(f"\tCORRECT")
    finally:
        test_done += 1
    
    print(f"\nCert PKI Issuer Fail")
    try:
        test_vectors_idd_configuration_cert_4_PKI_issuer(general_log_level)
    except AssertionError:
        print(f"\tFAILED")
    else:
        test_passed += 1
        print(f"\tCORRECT")
    finally:
        test_done += 1
    
    print(f"\nCert PKI Signature Fail")
    try:
        test_vectors_idd_configuration_cert_4_PKI_signature(general_log_level)
    except AssertionError:
        print(f"\tFAILED")
    else:
        test_passed += 1
        print(f"\tCORRECT")
    finally:
        test_done += 1

    print(f"\nCert PKI Revokated Fail")
    try:
        test_vectors_idd_configuration_cert_4_PKI_revokated(general_log_level)
    except AssertionError:
        print(f"\tFAILED")
    else:
        test_passed += 1
        print(f"\tCORRECT")
    finally:
        test_done += 1
    
    #------------------------------------------------------------------------------------

    print(f"\nCRL RCA Time Fail")
    try:
        test_vectors_idd_configuration_crl_1_time(general_log_level)
    except AssertionError:
        print(f"\tFAILED")
    else:
        test_passed += 1
        print(f"\tCORRECT")
    finally:
        test_done += 1
    
    print(f"\nCRL RCA Issuer Fail")
    try:
        test_vectors_idd_configuration_crl_1_issuer(general_log_level)
    except AssertionError:
        print(f"\tFAILED")
    else:
        test_passed += 1
        print(f"\tCORRECT")
    finally:
        test_done += 1

    print(f"\nCRL RCA Signature Fail")
    try:
        test_vectors_idd_configuration_crl_1_signature(general_log_level)
    except AssertionError:
        print(f"\tFAILED")
    else:
        test_passed += 1
        print(f"\tCORRECT")
    finally:
        test_done += 1

    #------------------------------------------------------------------------------------

    print(f"\nCRL SCA Time Fail")
    try:
        test_vectors_idd_configuration_crl_2_time(general_log_level)
    except AssertionError:
        print(f"\tFAILED")
    else:
        test_passed += 1
        print(f"\tCORRECT")
    finally:
        test_done += 1
    
    print(f"\nCRL SCA Issuer Fail")
    try:
        test_vectors_idd_configuration_crl_2_issuer(general_log_level)
    except AssertionError:
        print(f"\tFAILED")
    else:
        test_passed += 1
        print(f"\tCORRECT")
    finally:
        test_done += 1
    
    print(f"\nCRL SCA Signature Fail")
    try:
        test_vectors_idd_configuration_crl_2_signature(general_log_level)
    except AssertionError:
        print(f"\tFAILED")
    else:
        test_passed += 1
        print(f"\tCORRECT")
    finally:
        test_done += 1

    #------------------------------------------------------------------------------------

    print(f"\nCRL ICA Time Fail")
    try:
        test_vectors_idd_configuration_crl_3_time(general_log_level)
    except AssertionError:
        print(f"\tFAILED")
    else:
        test_passed += 1
        print(f"\tCORRECT")
    finally:
        test_done += 1
    
    print(f"\nCRL ICA Issuer Fail")
    try:
        test_vectors_idd_configuration_crl_3_issuer(general_log_level)
    except AssertionError:
        print(f"\tFAILED")
    else:
        test_passed += 1
        print(f"\tCORRECT")
    finally:
        test_done += 1

    print(f"\nCRL ICA Verify Fail")
    try:
        test_vectors_idd_configuration_crl_3_signature(general_log_level)
    except AssertionError:
        print(f"\tFAILED")
    else:
        test_passed += 1
        print(f"\tCORRECT")
    finally:
        test_done += 1
    #------------------------------------------------------------------------------------


    print('\n=====================================')
    print(f'\tTEST PASSED: {test_passed}/{test_done}')
    print('=====================================')
