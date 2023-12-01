import re
import logging

from typing import Tuple

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
