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
from osnma.input_formats.input_misc import ICDTestVectors
from osnma.input_formats.input_sbf import SBF
import osnma.utils.logger_factory as logger_factory


LOGS_PATH = Path(__file__).parent / 'metrics_live_recordings_logs/'


### get global params ###

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


### Configs ###

def icd_config_X(extra_config_dict=None, start_at_gst: Tuple[int, int] = None, log_level=logging.INFO):

    extra_config_dict = extra_config_dict if extra_config_dict else {}

    config_dict = {
        'console_log_level': log_level,
        'logs_path': LOGS_PATH,
        'scenario_path': Path(__file__).parent / 'scenarios/configuration_X/27_JUL_2023_GST_00_00_01_fixed.csv',
        'exec_path': Path(__file__).parent / 'scenarios/configuration_X/',
        'pubk_name': 'OSNMA_PublicKey_2.xml',
        'kroot_name': 'OSNMA_start_KROOT.txt',
        'stop_at_faf': True
    }
    config_dict.update(extra_config_dict)

    input_module = ICDTestVectors(config_dict['scenario_path'])
    osnma_r = OSNMAReceiver(input_module, config_dict)
    try:
        osnma_r.start(start_at_gst=start_at_gst)
    except Exception as e:
        print(e)
        pass
    first_gst, faf_gst, ttfaf = get_TTFAF_stats()
    print(f"TTFAF: {ttfaf}\t{first_gst}-{faf_gst}")
    return int(ttfaf)


def van_recording(extra_config_dict=None, start_at_gst: Tuple[int, int] = None, log_level=logging.INFO):

    extra_config_dict = extra_config_dict if extra_config_dict else {}

    config_dict = {
        'console_log_level': log_level,
        'logs_path': LOGS_PATH,
        'scenario_path': Path(__file__).parent / 'scenarios/van_back/van_back.sbf',
        'exec_path': Path(__file__).parent / 'scenarios/van_back/',
        'pubk_name': 'OSNMA_PublicKey.xml',
        'kroot_name': 'OSNMA_start_KROOT.txt',
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


### Extract data and plot ###

def get_ttfaf_matrix(run_config_function, wn, tow_range, save, numpy_file_name='ttfaf_matrix_last_run.npy'):

    base = {'log_console': False, 'do_hkroot_regen': True, 'do_crc_failed_extraction': False, 'do_tesla_key_regen': False}
    crc_extraction = {'log_console': False, 'do_hkroot_regen': True, 'do_crc_failed_extraction': True, 'do_tesla_key_regen': False}
    crc_and_tesla_extraction = {'log_console': False, 'do_hkroot_regen': True, 'do_crc_failed_extraction': True, 'do_tesla_key_regen': True}

    config_list = [base, crc_extraction, crc_and_tesla_extraction]

    ttfaf_matrix = np.zeros([len(config_list), tow_range.stop-tow_range.start])
    for i, config in enumerate(config_list):
        for j, tow in enumerate(tow_range):
            ttfaf = run_config_function(
                config,
                start_at_gst=(wn, tow))
            ttfaf_matrix[i][j] = ttfaf
        print(ttfaf_matrix[i])

    if save:
        np.save(numpy_file_name, ttfaf_matrix)

    return ttfaf_matrix


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


if __name__ == "__main__":

    # ttfaf = icd_config_X(
    #     {'log_console': True, 'do_hkroot_regen': True, 'do_crc_failed_extraction': True, 'do_tesla_key_regen': True},
    #     start_at_gst=(1248, 345622))
    # exit()

    sim_params = {
        "WN": 1248,
        "TOW_START": 345601,
        "TOW_STOP": 345601+300,
        "numpy_file_name": "ttfaf_matrix_config_X.npy",
        "function": icd_config_X
    }

    # sim_params = {
    #     "WN": 1256,
    #     "TOW_START": 599900,
    #     "TOW_STOP": 599900+300,
    #     "numpy_file_name": "ttfaf_matrix_van_recording.npy",
    #     "function": van_recording
    # }

    ttfaf_matrix = np.load(sim_params["numpy_file_name"])

    # ttfaf_matrix = get_ttfaf_matrix(sim_params["function"],
    #                                 sim_params["WN"],
    #                                 range(sim_params["TOW_START"], sim_params["TOW_STOP"]),
    #                                 True,
    #                                 numpy_file_name=sim_params["numpy_file_name"])

    plot_ttfaf(ttfaf_matrix, range(sim_params["TOW_START"], sim_params["TOW_STOP"]))
