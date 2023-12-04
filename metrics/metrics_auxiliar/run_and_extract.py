import re
import logging

from typing import Tuple

import numpy as np

from osnma.receiver.receiver import OSNMAReceiver
import osnma.utils.logger_factory as logger_factory

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

def run_with_config(config_dict, input_class, start_at_gst: Tuple[int, int] = None):

    input_module = input_class(config_dict['scenario_path'])
    osnma_r = OSNMAReceiver(input_module, config_dict)
    try:
        osnma_r.start(start_at_gst=start_at_gst)
    except Exception as e:
        print(e)
        pass
    first_gst, faf_gst, ttfaf = get_TTFAF_stats()
    print(f"TTFAF: {ttfaf}\t{first_gst}-{faf_gst}")
    return int(ttfaf)

def get_ttfaf_matrix(sim_params, optimizations_list, save):

    wn = sim_params["WN"]
    tow_range = range(sim_params["TOW_START"], sim_params["TOW_STOP"])
    numpy_file_name = sim_params["numpy_file_name"] if save else "ttfaf_matrix_last_run.npy"

    ttfaf_matrix = np.zeros([len(optimizations_list)+1, tow_range.stop-tow_range.start])
    ttfaf_matrix[0] = tow_range
    for i, config in enumerate(optimizations_list, start=1):
        for j, tow in enumerate(tow_range):
            run_config = sim_params["config_dict"]
            run_config.update(config)
            ttfaf = run_with_config(run_config, sim_params["input_module"], start_at_gst=(wn, tow))
            ttfaf_matrix[i][j] = ttfaf
        # print(ttfaf_matrix[i])
    # print(ttfaf_matrix)

    if save:
        np.save(numpy_file_name, ttfaf_matrix)

    return ttfaf_matrix

