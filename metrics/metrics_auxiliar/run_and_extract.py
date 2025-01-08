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
from osnma.input_formats.input_misc import ICDTestVectors


#########################################

def normal_run_and_exit(sim_params, test_vectors=False, copy_json_log=False):

    # Select correct input module
    if test_vectors:
        input_module = ICDTestVectors(sim_params["config_dict"]["scenario_path"])
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
    sim_params["config_dict"].update({'stop_at_faf': True, 'log_console': False, 'log_file': False})
    numpy_file_name = sim_params["numpy_file_name"] if save else "ttfaf_matrix_last_run.npy"

    ttfaf_matrix = np.zeros([len(optimizations_list)+1, tow_range.stop-tow_range.start])
    ttfaf_matrix[0] = tow_range
    for i, config in enumerate(tqdm(optimizations_list), start=1):
        run_config = sim_params["config_dict"].copy()
        run_config.update(config)
        for j, tow in enumerate(tqdm(tow_range, leave=False)):
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
    sim_params["config_dict"].update({'stop_at_faf': True, 'log_console': False, 'log_file': False})

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

    if save:
        numpy_file_name = sim_params["numpy_file_name"] if save else "ttfaf_matrix_last_run.npy"
        np.save(numpy_file_name, ttfaf_matrix)

    return ttfaf_matrix

