import sys
sys.path.insert(0, '..')
import re
import logging
import matplotlib.pyplot as plt
import numpy as np
import numpy.typing as npt

from pathlib import Path
from typing import Tuple

from osnma.receiver.receiver import OSNMAReceiver
from osnma.input_formats.input_sbf import SBF
import osnma.utils.logger_factory as logger_factory


LOGS_PATH = Path(__file__).parent / 'metrics_live_recordings_logs/'


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
    """
    Get the last file used for logging and extract the rellevant metrics
    :return: first_tow, faf_tow, ttfaf
    """
    base_logger, file_handler, log_filename = get_base_logger_and_file_handler()
    base_logger.removeHandler(file_handler)

    with open(log_filename, 'r') as log_file:
        log_text = log_file.read()
        first_tow = re.findall(r'First GST [0-9]+ ([0-9]+)', log_text)[0]
        faf_tow = re.findall(r'First Authenticated Fix at GST [0-9]+ ([0-9]+)', log_text)[0]
        ttfaf = re.findall(r'TTFAF ([0-9]+) seconds', log_text)[0]

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


def sbf_live_parc_leopold(extra_config_dict=None, start_at_gst: Tuple[int, int] = None, log_level=logging.INFO):

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

    input_module = SBF(config_dict['scenario_path'])
    osnma_r = OSNMAReceiver(input_module, config_dict)
    try:
        osnma_r.start(start_at_gst=start_at_gst)
    except Exception as e:
        print(e)
        pass
    first_gst, faf_gst, ttfaf = get_TTFAF_stats()
    print(f"TTFAF: {ttfaf}\t{first_gst}-{faf_gst}")
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


def plot_ttfaf(plot_ttfaf_vectors: npt.NDArray, tow_range: range):

    names = ["Base", "Tag extraction", "Tag and Tesla extraction"]

    fig, ax1 = plt.subplots(1, 1, figsize=(16, 9))
    for idx, (ttfaf_vector, config_name) in enumerate(zip(plot_ttfaf_vectors, names)):
        plt.plot(tow_range, ttfaf_vector+(0.15*idx), '*', label=config_name)

    plt.ylabel('Time [s]')
    plt.xticks(tow_range[::2], [t % 30 for t in tow_range[::2]])

    for t in tow_range:
        if t % 30 == 0:
            plt.axvline(x=t, ymin=0.01, ymax=0.99, color='r', ls='-', alpha=0.5)

    plt.grid()
    plt.legend(loc='upper right')
    plt.show()


def get_ttfaf_data_for_parc_leopold(wn, tow_range, save):

    base = {'log_console': False, 'do_hkroot_regen': True, 'do_crc_failed_extraction': False, 'do_tesla_key_regen': False}
    crc_extraction = {'log_console': False, 'do_hkroot_regen': True, 'do_crc_failed_extraction': True, 'do_tesla_key_regen': False}
    crc_and_tesla_extraction = {'log_console': False, 'do_hkroot_regen': True, 'do_crc_failed_extraction': True, 'do_tesla_key_regen': True}

    config_list = [base, crc_extraction, crc_and_tesla_extraction]

    ttfaf_matrix = np.zeros([len(config_list), tow_range.stop-tow_range.start])
    for i, config in enumerate(config_list):
        for j, tow in enumerate(tow_range):
            ttfaf = sbf_live_parc_leopold(
                config,
                start_at_gst=(wn, tow))
            ttfaf_matrix[i][j] = ttfaf
        print(ttfaf_matrix[i])

    if save:
        np.save("ttfaf_vectors_leopold_all", ttfaf_matrix)

    return ttfaf_matrix


if __name__ == "__main__":

    # ttfaf = sbf_live_parc_leopold(
    #     {'log_console': True, 'do_hkroot_regen': True, 'do_crc_failed_extraction': True, 'do_tesla_key_regen': True},
    #     start_at_tow=52412)
    #
    # exit()

    WN = 1210
    TOW_START = 52268
    TOW_STOP = TOW_START + 300
    tow_range = range(TOW_START, TOW_STOP)

    ttfaf_matrix = np.load("ttfaf_vectors_leopold_all.npy")

    # ttfaf_matrix = get_ttfaf_data_for_parc_leopold(WN, tow_range, False)

    plot_ttfaf(ttfaf_matrix, tow_range)
