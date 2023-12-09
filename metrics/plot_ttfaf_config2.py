import sys
sys.path.insert(0, '..')
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from osnma.input_formats.input_misc import ICDTestVectors
from metrics_auxiliar.run_and_extract import get_ttfaf_matrix
from metrics_auxiliar.predefined_plots import plot_ttfaf, plot_cdf

DATA_FOLDER = Path(__file__).parent / 'scenarios/configuration_2/'

sim_params = {
    "WN": 1248,
    "TOW_START": 345601,
    "TOW_STOP": 345601 + 300,
    "input_module": ICDTestVectors,
    "name": "Hot Start TTFAF - ICD Config 2",
    "numpy_file_name": DATA_FOLDER / "ttfaf_matrix_config_2.npy",
    "config_dict": {
        'scenario_path': DATA_FOLDER / '27_JUL_2023_GST_00_00_01_fixed.csv',
        'exec_path': DATA_FOLDER,
        'pubk_name': 'OSNMA_PublicKey_2.xml',
        'kroot_name': 'OSNMA_start_KROOT.txt',
        'stop_at_faf': True,
        'log_console': False,
        'log_file': False
    }
}

if __name__ == "__main__":

    options = {
        "IOD data link": {'do_crc_failed_extraction': False, 'do_tesla_key_regen': False, 'TL': 30},
        "IOD data link and Page level processing": {'do_crc_failed_extraction': True, 'do_tesla_key_regen': True, 'TL': 30},
        "IOD data link and Page level processing - TL 29s": {'do_crc_failed_extraction': True, 'do_tesla_key_regen': True, 'TL': 29},
        "IOD data link and Page level processing - TL 27s": {'do_crc_failed_extraction': True, 'do_tesla_key_regen': True, 'TL': 27},
        "IOD data link and Page level processing - TL 25s": {'do_crc_failed_extraction': True, 'do_tesla_key_regen': True, 'TL': 25},
    }

    #ttfaf_matrix = get_ttfaf_matrix(sim_params, options.values(), True)
    ttfaf_matrix = np.load(sim_params["numpy_file_name"])

    plot_ttfaf(ttfaf_matrix, options.keys(), sim_params["name"])
    plot_cdf(ttfaf_matrix, options.keys(), sim_params["name"])

    plt.show()

