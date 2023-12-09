from typing import Tuple

import numpy as np
from tqdm import tqdm

from osnma.receiver.receiver import OSNMAReceiver
from osnma.input_formats.input_sbf import SBFMetrics

def run_with_config(config_dict, input_class, start_at_gst: Tuple[int, int] = None):

    input_module = input_class(config_dict['scenario_path'])
    osnma_r = OSNMAReceiver(input_module, config_dict)
    try:
        ttfaf, first_tow, faf_tow = osnma_r.start(start_at_gst=start_at_gst)
    except Exception as e:
        print(e)
        ttfaf = first_tow = faf_tow = None
    #print(f"TTFAF: {ttfaf}\t{first_tow}-{faf_tow}")
    return ttfaf

def get_ttfaf_matrix(sim_params, optimizations_list, save):

    wn = sim_params["WN"]
    tow_range = range(sim_params["TOW_START"], sim_params["TOW_STOP"])
    numpy_file_name = sim_params["numpy_file_name"] if save else "ttfaf_matrix_last_run.npy"

    ttfaf_matrix = np.zeros([len(optimizations_list)+1, tow_range.stop-tow_range.start])
    ttfaf_matrix[0] = tow_range
    for i, config in enumerate(tqdm(optimizations_list), start=1):
        for j, tow in enumerate(tqdm(tow_range, leave=False)):
            run_config = sim_params["config_dict"]
            run_config.update(config)
            ttfaf = run_with_config(run_config, sim_params["input_module"], start_at_gst=(wn, tow))
            ttfaf_matrix[i][j] = ttfaf

    if save:
        np.save(numpy_file_name, ttfaf_matrix)

    return ttfaf_matrix

#########################################

def run_with_configSBF(config_dict, sbfmetric_input, start_at_gst: Tuple[int, int]):

    osnma_r = OSNMAReceiver(sbfmetric_input, config_dict)
    try:
        ttfaf, first_tow, faf_tow = osnma_r.start(start_at_gst=start_at_gst)
    except Exception as e:
        print(e)
        ttfaf = first_tow = faf_tow = None
    # print(f"TTFAF: {ttfaf}\t{first_tow}-{faf_tow}")
    return ttfaf

def get_ttfaf_matrixSBF(sim_params, optimizations_list, save):

    wn = sim_params["WN"]
    tow_range = range(sim_params["TOW_START"], sim_params["TOW_STOP"])

    ttfaf_matrix = np.zeros([len(optimizations_list)+1, tow_range.stop-tow_range.start])
    ttfaf_matrix[0] = tow_range

    file_handler = open(sim_params["config_dict"]["scenario_path"], 'br')
    sbfmetric_input = SBFMetrics(file_handler)

    for i, config in enumerate(tqdm(optimizations_list), start=1):
        sbfmetric_input.file_goto(0)
        run_config = sim_params["config_dict"]
        run_config.update(config)
        for j, tow in enumerate(tqdm(tow_range, leave=False)):
            sbfmetric_input.start_tow = tow
            ttfaf = run_with_configSBF(run_config, sbfmetric_input, (wn, tow))
            ttfaf_matrix[i][j] = ttfaf
            sbfmetric_input.file_goto(sbfmetric_input.start_pos)
    file_handler.close()

    if save:
        numpy_file_name = sim_params["numpy_file_name"] if save else "ttfaf_matrix_last_run.npy"
        np.save(numpy_file_name, ttfaf_matrix)

    return ttfaf_matrix

