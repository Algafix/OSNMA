import sys
sys.path.insert(0, '..')
import os
import shutil
from pathlib import Path

from typing import Tuple

import numpy as np
from tqdm import tqdm

from osnma.receiver.receiver import OSNMAReceiver
from osnma.input_formats.input_sbf import SBFMetrics, SBF
from osnma.input_formats.input_misc import ICDTestVectors, AndroidGNSSLog


#########################################

def normal_run_and_exit(sim_params, test_vectors=False, android_log=False, copy_json_log=False):

    # Select correct input module
    if test_vectors:
        input_module = ICDTestVectors(sim_params["config_dict"]["scenario_path"])
    elif android_log:
        input_module = AndroidGNSSLog(sim_params["config_dict"]["scenario_path"])
    else:
        input_module = SBF(sim_params["config_dict"]["scenario_path"])

    # Overwrite configuration to not stop at faf and generate logs
    run_config = sim_params["config_dict"]
    run_config['stop_at_faf'] = False
    run_config['log_console'] = True
    run_config['log_file'] = True

    # Select start time
    wn = sim_params["WN"]
    tow = sim_params["TOW_START"]

    # Run
    osnma_r = OSNMAReceiver(input_module, run_config)
    osnma_r.start(start_at_gst=(wn, tow))

    if copy_json_log:
        directories = sorted([d for d in Path('.').iterdir() if d.is_dir() and d.name.startswith("logs_")])
        last_directory_created = directories[-1]
        shutil.copy(last_directory_created/"status_log.json", "status_log.json")
        shutil.rmtree(last_directory_created)

    exit()

#########################################

def get_kroot_and_exit(sim_params):
    input_module = SBF(sim_params["config_dict"]["scenario_path"])
    run_config = sim_params["config_dict"]
    run_config['stop_at_faf'] = True
    run_config['log_file'] = True
    run_config['log_console'] = True
    osnma_r = OSNMAReceiver(input_module, run_config)
    osnma_r.start()
    try:
        os.rename(Path(run_config['exec_path']) / "OSNMA_last_KROOT.txt", Path(run_config['exec_path']) / "OSNMA_start_KROOT.txt")
    except Exception:
        print(f"[-] No last KROOT file, are you running in hot start already?")

    exit()

#########################################

def filter_nan_in_ttfaf(ttfaf_matrix, sim_params, optimizations):
    """
    Drop all columns of all configurations from the ToW where a NaN is detected. Thus, al configuration have the same
    epochs. If a configuration has all NaN, they are replaced by all 0.
    """

    min_nan_indexes = []
    for i in np.arange(ttfaf_matrix.shape[0]-1):
        nan_positions = np.argwhere(np.isnan(ttfaf_matrix[i+1,:]))
        if nan_positions.size != 0:
            min_nan_index = np.min(nan_positions)
            if min_nan_index == 0:
                print(f"No TTFAF possible for '{optimizations[i]}'. Replaced with all 0 for plots.")
                ttfaf_matrix[i+1] = np.zeros(ttfaf_matrix[i+1].size)
            else:
                min_nan_indexes.append(min_nan_index)

    if len(min_nan_indexes) == 0:
        ttfaf_no_nan_matrix = ttfaf_matrix
    else:
        global_min_nan_index = min(min_nan_indexes)
        ttfaf_no_nan_matrix = ttfaf_matrix[:, :global_min_nan_index]
        last_tow = int(ttfaf_no_nan_matrix[0, -1])
        print(f"Some configurations could not get at TTFAF before the end of the file!\n"
              f"Requested last ToW: {sim_params['TOW_STOP']} - Effective Last ToW: {last_tow} - Effective time processed: {last_tow - sim_params['TOW_START']}")

    return ttfaf_no_nan_matrix

def run_with_config(config_dict, input_class, start_at_gst: Tuple[int, int] = None):

    input_module = input_class(config_dict['scenario_path'])
    osnma_r = OSNMAReceiver(input_module, config_dict)
    try:
        ttfaf, first_tow, faf_tow = osnma_r.start(start_at_gst=start_at_gst)
    except TypeError as e:
        # No TTFAF, probably due to file length
        ttfaf = None
    except Exception as e:
        print(e)
        ttfaf = None
    return ttfaf

def get_ttfaf_matrix(sim_params, optimizations, save):

    wn = sim_params["WN"]
    tow_range = range(sim_params["TOW_START"], sim_params["TOW_STOP"])
    sim_params["config_dict"].update({'stop_at_faf': True, 'log_console': False, 'log_file': False})
    numpy_file_name = sim_params["numpy_file_name"] if save else "ttfaf_matrix_last_run.npy"
    optimizations_list = list(optimizations.values())
    optimizations_names = list(optimizations.keys())

    ttfaf_matrix = np.zeros([len(optimizations_list)+1, tow_range.stop-tow_range.start])
    ttfaf_matrix[0] = tow_range
    for i, config in enumerate(tqdm(optimizations_list), start=1):
        run_config = sim_params["config_dict"].copy()
        run_config.update(config)
        for j, tow in enumerate(tqdm(tow_range, leave=False)):
            ttfaf = run_with_config(run_config, sim_params["input_module"], start_at_gst=(wn, tow))
            ttfaf_matrix[i][j] = ttfaf

    ttfaf_no_nan_matrix = filter_nan_in_ttfaf(ttfaf_matrix, sim_params, optimizations_names)

    if save:
        np.save(numpy_file_name, ttfaf_no_nan_matrix)

    return ttfaf_no_nan_matrix

#########################################

def run_with_configSBF(config_dict, sbfmetric_input, start_at_gst: Tuple[int, int]):

    osnma_r = OSNMAReceiver(sbfmetric_input, config_dict)
    try:
        ttfaf, first_tow, faf_tow = osnma_r.start(start_at_gst=start_at_gst)
    except TypeError as e:
        # No TTFAF, probably due to file length
        ttfaf = None
    except Exception as e:
        print(e)
        ttfaf = None
    return ttfaf

def get_ttfaf_matrixSBF(sim_params, optimizations, save):

    wn = sim_params["WN"]
    tow_range = range(sim_params["TOW_START"], sim_params["TOW_STOP"])
    sim_params["config_dict"].update({'stop_at_faf': True, 'log_console': False, 'log_file': False})
    optimizations_list = list(optimizations.values())
    optimizations_names = list(optimizations.keys())

    ttfaf_matrix = np.zeros([len(optimizations_list)+1, tow_range.stop-tow_range.start])
    ttfaf_matrix[0] = tow_range

    file_handler = open(sim_params["config_dict"]["scenario_path"], 'br')
    sbfmetric_input = SBFMetrics(file_handler)

    for i, config in enumerate(tqdm(optimizations_list), start=1):
        sbfmetric_input.file_goto(0)
        run_config = sim_params["config_dict"].copy()
        run_config.update(config)
        for j, tow in enumerate(tqdm(tow_range, leave=False)):
            sbfmetric_input.start_tow = tow
            ttfaf = run_with_configSBF(run_config, sbfmetric_input, (wn, tow))
            ttfaf_matrix[i][j] = ttfaf
            sbfmetric_input.file_goto(sbfmetric_input.start_pos)
    file_handler.close()

    ttfaf_no_nan_matrix = filter_nan_in_ttfaf(ttfaf_matrix, sim_params, optimizations_names)

    if save:
        numpy_file_name = sim_params["numpy_file_name"] if save else "ttfaf_matrix_last_run.npy"
        np.save(numpy_file_name, ttfaf_no_nan_matrix)

    return ttfaf_no_nan_matrix

