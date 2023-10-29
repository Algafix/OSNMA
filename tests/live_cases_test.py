import sys
sys.path.insert(0, '..')
import re
import logging
import matplotlib.pyplot as plt

from pathlib import Path

from osnma.receiver.receiver import OSNMAReceiver
from osnma.input_formats.input_sbf import SBF
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


def get_TTFAF_stats():
    base_logger, file_handler, log_filename = get_base_logger_and_file_handler()
    base_logger.removeHandler(file_handler)

    with open(log_filename, 'r') as log_file:
        log_text = log_file.read()
        first_tow = re.findall(r'FIRST TOW ([0-9]+)', log_text)[0]
        faf_tow = re.findall(r'FIRST AUTHENTICATED FIX [0-9]+ ([0-9]+)', log_text)[0]
        ttfaf = re.findall(r'TTFAF ([0-9]+)', log_text)[0]

    return first_tow, faf_tow, ttfaf


def print_stats():

    base_logger, file_handler, log_filename = get_base_logger_and_file_handler()
    base_logger.removeHandler(file_handler)

    with open(log_filename, 'r') as log_file:
        log_text = log_file.read()

        tags_auth = len(re.findall(r'Tag AUTHENTICATED', log_text))
        data_auth = len(re.findall(r'INFO .* AUTHENTICATED: ADKD', log_text))
        kroot_auth = len(re.findall(r'INFO .*KROOT.*\n\tAUTHENTICATED\n', log_text))

        total_tesla_keys = re.findall(r'Tesla Key Authenticated ([0-9]+ [0-9]+)', log_text)
        nominal_tesla_keys = re.findall(r'Tesla Key Authenticated ([0-9]+ [0-9]+)\n', log_text)
        regen_tesla_keys = re.findall(r'Tesla Key Authenticated ([0-9]+ [0-9]+) .* Regenerated', log_text)
        total_sf_with_tesla_key = set(total_tesla_keys)
        total_sf_with_nominal_tesla_key = set(nominal_tesla_keys)
        total_sf_with_regen_tesla_key = set(regen_tesla_keys)
        total_sf_with_only_regen_tesla_key = {i for i in total_sf_with_regen_tesla_key if i not in total_sf_with_nominal_tesla_key}

        broken_kroot = len(re.findall('WARNING.*Broken HKROOT', log_text))
        crc_failed = len(re.findall('WARNING.*CRC', log_text))
        warnings = len(re.findall('WARNING', log_text))
        errors = len(re.findall('ERROR', log_text))

    print('')
    print(f"Tags Authenticated: {tags_auth}")
    print(f"KROOT Authenticated: {kroot_auth}")
    print(f"Nominal Tesla Keys: {len(nominal_tesla_keys)}")
    print(f"Regenerated Tesla Keys: {len(regen_tesla_keys)}")
    print(f"SF with TK: {len(total_sf_with_tesla_key)}")
    print(f"SF with only regen TK: {len(total_sf_with_only_regen_tesla_key)}")
    print(f"Warnings: {warnings}")
    print(f"Errors: {errors}")


def sbf_live_parc_leopold(extra_config_dict=None, start_at_tow=0, log_level=logging.INFO):

    extra_config_dict = extra_config_dict if extra_config_dict else {}

    config_dict = {
        'console_log_level': log_level,
        'logs_path': LOGS_PATH,
        'scenario_path': Path(__file__).parent / 'scenarios/live_parc_leopold/parc_leopold.sbf',
        'exec_path': Path(__file__).parent / 'scenarios/live_parc_leopold',
        'pubk_name': 'OSNMA_PublicKey.xml',
        'kroot_name': 'OSNMA_KROOT_for_hot_start.txt',
        'stop_at_faf': True
    }
    config_dict.update(extra_config_dict)

    input_module = SBF(config_dict['scenario_path'], start_at_tow)
    osnma_r = OSNMAReceiver(input_module, config_dict)
    try:
        osnma_r.start()
    except Exception as e:
        pass
    first_tow, faf_tow, ttfaf = get_TTFAF_stats()
    print(f"TTFAF: {ttfaf}\t{first_tow}-{faf_tow}")
    return int(ttfaf)


def sbf_live_palace_to_parlament(extra_config_dict=None, log_level=logging.INFO):

    extra_config_dict = extra_config_dict if extra_config_dict else {}

    config_dict = {
        'console_log_level': log_level,
        'logs_path': LOGS_PATH,
        'scenario_path': Path(__file__).parent / 'scenarios/live_palace_to_parlament/palace_to_parlament.sbf',
        'exec_path': Path(__file__).parent / 'scenarios/live_palace_to_parlament',
        'pubk_name': 'OSNMA_PublicKey.xml'
    }
    config_dict.update(extra_config_dict)

    input_module = SBF(config_dict['scenario_path'])
    osnma_r = OSNMAReceiver(input_module, config_dict)

    osnma_r.start()

    print_stats()


def sbf_live_manneken(extra_config_dict=None, log_level=logging.INFO):

    extra_config_dict = extra_config_dict if extra_config_dict else {}

    config_dict = {
        'console_log_level': log_level,
        'logs_path': LOGS_PATH,
        'scenario_path': Path(__file__).parent / 'scenarios/live_to_manneken/to_manneken.sbf',
        'exec_path': Path(__file__).parent / 'scenarios/live_to_manneken',
        'pubk_name': 'OSNMA_PublicKey.xml'
    }
    config_dict.update(extra_config_dict)

    input_module = SBF(config_dict['scenario_path'])
    osnma_r = OSNMAReceiver(input_module, config_dict)

    osnma_r.start()

    print_stats()


if __name__ == "__main__":

    ttfaf_list = []
    for tow in range(52268, 52368):
        ttfaf = sbf_live_parc_leopold(
            {'log_console': False, 'do_hkroot_regen': True, 'do_crc_failed_extraction': True, 'do_tesla_key_regen': True},
            start_at_tow=tow)
        ttfaf_list.append(ttfaf)
    print(ttfaf_list)

    # ttfaf_list = [82, 81, 80, 79, 77, 77, 76, 75, 73, 73, 71, 71, 69, 69, 68, 67, 96, 95, 94, 93, 92, 91, 90, 89, 87, 87, 85, 85, 84, 83, 82, 81, 80, 79, 78, 77, 75, 75, 74, 73, 71, 71, 69, 69, 68, 67, 96, 95, 94, 93, 92, 91, 89, 89, 88, 87, 85, 85, 84, 83, 82, 81, 80, 79, 78, 77, 75, 75, 74, 73, 71, 71, 69, 69, 67, 67, 96, 95, 94, 93, 92, 91, 90, 89, 87, 87, 86, 85, 83, 83, 81, 81, 80, 79, 78, 77, 75, 75, 73, 73]
    # plt.plot(ttfaf_list)
    # plt.ylabel('Time [s]')
    # plt.show()

    # ONLY CONSECUTIVE
    #   Tags Authenticated: 1165
    #   KROOT Authenticated: 27
    #   Nominal Tesla Keys: 381
    #   Regenerated Tesla Keys: 0
    #   SF with TK: 159
    #   SF with only TK: 0
    #   Warnings: 3894
    #   Errors: 0

    # HKROOT REGEN
    #   Tags Authenticated: 1165
    #   KROOT Authenticated: 33
    #   Nominal Tesla Keys: 381
    #   Regenerated Tesla Keys: 0
    #   SF with TK: 159
    #   SF with only TK: 0
    #   Warnings: 3894
    #   Errors: 0

    # HKROOT REGEN, TAG EXTRACTION
    #   Tags Authenticated: 1529
    #   KROOT Authenticated: 33
    #   Nominal Tesla Keys: 505
    #   Regenerated Tesla Keys: 0
    #   SF with TK: 170
    #   SF with only TK: 0
    #   Warnings: 3894
    #   Errors: 3 - TAG0

    # HKROOT REGEN, TAG EXTRACTION, TESLA REGEN
    #   Tags Authenticated: 1529
    #   KROOT Authenticated: 33
    #   Nominal Tesla Keys: 505
    #   Regenerated Tesla Keys: 7
    #   SF with TK: 170
    #   SF with only TK: 0
    #   Warnings: 3894
    #   Errors: 3 - TAG0

#############################################################

    #sbf_live_palace_to_parlament({'do_hkroot_regen': True, 'do_crc_failed_extraction': True, 'do_tesla_key_regen': True})

    # ONLY CONSECUTIVE
    #   Tags Authenticated: 1498
    #   KROOT Authenticated: 33
    #   Nominal Tesla Keys: 540
    #   Regenerated Tesla Keys: 8
    #   SF with TK: 190
    #   SF with only TK: 0
    #   Warnings: 4554
    #   Errors: 1

    # HKROOT REGEN
    #   Tags Authenticated: 1498
    #   KROOT Authenticated: 38
    #   Nominal Tesla Keys: 540
    #   Regenerated Tesla Keys: 8
    #   SF with TK: 190
    #   SF with only TK: 0
    #   Warnings: 4554
    #   Errors: 1 - TAG0

    # HKROOT REGEN, TAG EXTRACTION
    #   Tags Authenticated: 1966
    #   KROOT Authenticated: 38
    #   Nominal Tesla Keys: 594
    #   Regenerated Tesla Keys: 0
    #   SF with TK: 204
    #   SF with only TK: 0
    #   Warnings: 4554
    #   Errors: 4 - TAG0

    # HKROOT REGEN, TESLA REGEN, TAG EXTRACTION
    #   Tags Authenticated: 1966
    #   KROOT Authenticated: 38
    #   Nominal Tesla Keys: 594
    #   Regenerated Tesla Keys: 8
    #   SF with TK: 204
    #   SF with only TK: 0
    #   Warnings: 4554
    #   Errors: 4 - TAG0

#############################################################

    #sbf_live_manneken({'do_hkroot_regen': True, 'do_crc_failed_extraction': True, 'do_tesla_key_regen': True})

    # ONLY CONSECUTIVE
    #   Tags Authenticated: 654
    #   KROOT Authenticated: 10
    #   Nominal Tesla Keys: 148
    #   Regenerated Tesla Keys: 0
    #   SF with TK: 96
    #   SF with only TK: 0
    #   Warnings: 3909
    #   Errors: 3

    # HKROOT REGEN
    #   Tags Authenticated: 665
    #   KROOT Authenticated: 12
    #   Nominal Tesla Keys: 156
    #   Regenerated Tesla Keys: 0
    #   SF with TK: 102
    #   SF with only TK: 0
    #   Warnings: 3909
    #   Errors: 3 - TAG0

    # HKROOT REGEN, TAG EXTRACTION
    #   Tags Authenticated: 870
    #   KROOT Authenticated: 12
    #   Nominal Tesla Keys: 221
    #   Regenerated Tesla Keys: 0
    #   SF with TK: 129
    #   SF with only TK: 0
    #   Warnings: 3909
    #   Errors: 3 - TAG0

    # HKROOT REGEN, TESLA REGEN, TAG EXTRACTION
    #   Tags Authenticated: 870
    #   KROOT Authenticated: 12
    #   Nominal Tesla Keys: 221
    #   Regenerated Tesla Keys: 0
    #   SF with TK: 129
    #   SF with only TK: 0
    #   Warnings: 3909
    #   Errors: 3 - TAG0
