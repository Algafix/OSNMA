import sys
sys.path.insert(0, '..')
import re
import logging
from pathlib import Path

from osnma.receiver.receiver import OSNMAReceiver
from osnma.receiver.input_sbf import SBF
import osnma.utils.logger_factory as logger_factory
LOGS_PATH = Path(__file__).parent / 'live_cases_logs/'


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


def print_stats():

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

    print('')
    print(f"Tags Authenticated: {tags_auth}")
    print(f"KROOT Authenticated: {kroot_auth}")
    print(f"Warnings: {warnings}")
    print(f"Errors: {errors}")


def sbf_live_parc_leopold(log_level=logging.INFO):

    config_dict = {
        'console_log_level': log_level,
        'logs_path': LOGS_PATH,
        'scenario_path': Path(__file__).parent / 'scenarios/live_parc_leopold/parc_leopold.sbf',
        'exec_path': Path(__file__).parent / 'scenarios/live_parc_leopold',
        'pubk_name': 'OSNMA_PublicKey.xml'
    }

    input_module = SBF(config_dict['scenario_path'])
    osnma_r = OSNMAReceiver(input_module, config_dict)

    osnma_r.start()

    print_stats()


def sbf_live_palace_to_parlament(log_level=logging.INFO):

    config_dict = {
        'console_log_level': log_level,
        'logs_path': LOGS_PATH,
        'scenario_path': Path(__file__).parent / 'scenarios/live_palace_to_parlament/palace_to_parlament.sbf',
        'exec_path': Path(__file__).parent / 'scenarios/live_palace_to_parlament',
        'pubk_name': 'OSNMA_PublicKey.xml'
    }

    input_module = SBF(config_dict['scenario_path'])
    osnma_r = OSNMAReceiver(input_module, config_dict)

    osnma_r.start()

    print_stats()


def sbf_live_manneken(log_level=logging.INFO):

    config_dict = {
        'console_log_level': log_level,
        'logs_path': LOGS_PATH,
        'scenario_path': Path(__file__).parent / 'scenarios/live_to_manneken/to_manneken.sbf',
        'exec_path': Path(__file__).parent / 'scenarios/live_to_manneken',
        'pubk_name': 'OSNMA_PublicKey.xml'
    }

    input_module = SBF(config_dict['scenario_path'])
    osnma_r = OSNMAReceiver(input_module, config_dict)

    osnma_r.start()

    print_stats()


if __name__ == "__main__":

    sbf_live_parc_leopold()

    # ONLY CONSECUTIVE
    #   Tags Authenticated: 1165
    #   KROOT Authenticated: 27
    #   Warnings: 3636
    #   Errors: 0

    # HKROOT REGEN
    #   Tags Authenticated: 1165
    #   KROOT Authenticated: 33
    #   Warnings: 3894
    #   Errors: 0

    # HKROOT REGEN, TAG EXTRACTION
    #   Tags Authenticated: 1529
    #   KROOT Authenticated: 33
    #   Warnings: 3894
    #   Errors: 3 - TAG0

    # HKROOT REGEN, TESLA REGEN, TAG EXTRACTION
    #   Tags Authenticated: 1529
    #   KROOT Authenticated: 33
    #   Warnings: 3894
    #   Errors: 3 - TAG0

#############################################################

    #sbf_live_palace_to_parlament()

    # ONLY CONSECUTIVE
    #   Tags Authenticated: 1498
    #   KROOT Authenticated: 33
    #   Warnings: 4245
    #   Errors: 1

    # HKROOT REGEN
    #   Tags Authenticated: 1498
    #   KROOT Authenticated: 38
    #   Warnings: 4554
    #   Errors: 1 - TAG0

    # HKROOT REGEN, TAG EXTRACTION
    #   Tags Authenticated: 1966
    #   KROOT Authenticated: 38
    #   Warnings: 4554
    #   Errors: 4 - TAG0

    # HKROOT REGEN, TESLA REGEN, TAG EXTRACTION
    #   Tags Authenticated: 1966
    #   KROOT Authenticated: 38
    #   Warnings: 4554
    #   Errors: 4 - TAG0

#############################################################

    #sbf_live_manneken()

    # ONLY CONSECUTIVE
    #   Tags Authenticated: 654
    #   KROOT Authenticated: 10
    #   Warnings: 3797
    #   Errors: 19
    #   Check errors. HKROOT takes a lot. The oldest saved MACSEQ and tags adkd 0 and 4 fail auth.
    #   Cant be a data problem because MACSEQ fails. ADKD 12 is fine. Change of kroot?

    # HKROOT REGEN
    #   Tags Authenticated: 665
    #   KROOT Authenticated: 12
    #   Warnings: 3909
    #   Errors: 3 - TAG0

    # HKROOT REGEN, TAG EXTRACTION
    #   Tags Authenticated: 870
    #   KROOT Authenticated: 12
    #   Warnings: 3909
    #   Errors: 3 - TAG0

    # HKROOT REGEN, TESLA REGEN, TAG EXTRACTION
    #   Tags Authenticated: 870
    #   KROOT Authenticated: 12
    #   Warnings: 3909
    #   Errors: 3 - TAG0
