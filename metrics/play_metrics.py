import sys
sys.path.insert(0, '..')
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from osnma.input_formats.input_sbf import SBF
from osnma.input_formats.input_misc import ICDTestVectors

from metrics_auxiliar.run_and_extract import get_ttfaf_matrix
from metrics_auxiliar.predefined_plots import plot_ttfaf, plot_cdf

LOGS_PATH = Path(__file__).parent / 'metrics_live_recordings_logs/'

DATA_FOLDER_PARK = Path(__file__).parent / 'scenarios/park_and_eu/'
sim_params_park = {
    "WN": 1267,
    "TOW_START": 35400,
    "TOW_STOP": 35400+100,
    "input_module": SBF,
    "name": "Hot Start TTFAF - Park and EU District",
    "numpy_file_name": DATA_FOLDER_PARK / "play.npy",
    "config_dict": {
        'logs_path': LOGS_PATH,
        'scenario_path': DATA_FOLDER_PARK / 'park_and_eu_inav.sbf',
        'exec_path': DATA_FOLDER_PARK,
        'pubk_name': 'OSNMA_PublicKey.xml',
        'kroot_name': 'OSNMA_start_KROOT.txt',
        'stop_at_faf': True,
        'log_console': False
    }
}

DATA_FOLDER_ICD = Path(__file__).parent / 'scenarios/configuration_2/'
sim_params_icd = {
    "WN": 1248,
    "TOW_START": 345601,
    "TOW_STOP": 345601+100,
    "input_module": ICDTestVectors,
    "name": "Hot Start TTFAF - ICD Config 2",
    "numpy_file_name": DATA_FOLDER_ICD / "play.npy",
    "config_dict": {
        'logs_path': LOGS_PATH,
        'scenario_path': DATA_FOLDER_ICD / '27_JUL_2023_GST_00_00_01_fixed.csv',
        'exec_path': DATA_FOLDER_ICD,
        'pubk_name': 'OSNMA_PublicKey_2.xml',
        'kroot_name': 'OSNMA_start_KROOT.txt',
        'stop_at_faf': True,
        'log_console': False
    }
}

if __name__ == "__main__":

    options = {
        "No Optimization": {'do_crc_failed_extraction': False, 'do_tesla_key_regen': False, 'TL': 30},
        "Page level Tag processing and Key reconstruction": {'do_crc_failed_extraction': True, 'do_tesla_key_regen': True, 'TL': 30},
        "Page level Tag processing and Key reconstruction - TL 28s": {'do_crc_failed_extraction': True, 'do_tesla_key_regen': True, 'TL': 28},
        "Page level Tag processing and Key reconstruction - TL 1s": {'do_crc_failed_extraction': True, 'do_tesla_key_regen': True, 'TL': 1}
    }
    # options = {
    #     "TL 31s": {'do_crc_failed_extraction': True, 'do_tesla_key_regen': True, 'TL': 31},
    #     "TL 30s": {'do_crc_failed_extraction': True, 'do_tesla_key_regen': True, 'TL': 30}
    # }

    sim_params = sim_params_icd
    #sim_params = sim_params_park

    ttfaf_matrix = get_ttfaf_matrix(sim_params, options.values(), True)
    #ttfaf_matrix = np.load(sim_params["numpy_file_name"])

    plot_ttfaf(ttfaf_matrix, options.keys(), sim_params["name"])
    plot_cdf(ttfaf_matrix, options.keys(), sim_params["name"])

    plt.show()
