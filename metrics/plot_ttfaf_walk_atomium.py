import sys
sys.path.insert(0, '..')
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from metrics_auxiliar.run_and_extract import get_ttfaf_matrixSBF
from metrics_auxiliar.predefined_plots import plot_ttfaf, plot_cdf, plot_per_subframe, print_pki
# 2291 39804 -> 03/12/2023 - 11:03:24 UTC
# 2291 42233 -> 03/12/2023 - 11:43:53 UTC

DATA_FOLDER = Path(__file__).parent / 'scenarios/walk_atomium/'

sim_params = {
    "WN": 1267,
    "TOW_START": 39804,
    "TOW_STOP": 42233,
    "name": "Hot Start TTFAF - Walk in Atomium",
    "numpy_file_name": DATA_FOLDER / "ttfaf_matrix_walk_atomium_COP.npy",
    "config_dict": {
        'scenario_path': DATA_FOLDER / 'walk_atomium_inav.sbf',
        'exec_path': DATA_FOLDER,
        'pubk_name': 'OSNMA_PublicKey.xml',
        'kroot_name': 'OSNMA_start_KROOT.txt',
        'stop_at_faf': True,
        'log_console': False,
        'log_file': False
    }
}

if __name__ == "__main__":

    options = {
        "IOD data link. TL 30s": {'do_crc_failed_extraction': False, 'do_tesla_key_regen': False, 'TL': 30},
        "IOD data link and Page level processing. TL 25s": {'do_crc_failed_extraction': True, 'do_tesla_key_regen': True, 'TL': 25},
        "IOD and COP data link and Page level processing. TL 17s": {'do_crc_failed_extraction': True, 'do_tesla_key_regen': True, 'DO_COP_LINK_OPTIMIZATION': True, 'TL': 17},
    }

    #ttfaf_matrix = get_ttfaf_matrixSBF(sim_params, options.values(), True)
    ttfaf_matrix = np.load(sim_params["numpy_file_name"])

    plot_ttfaf(ttfaf_matrix, options.keys(), sim_params["name"], DATA_FOLDER)
    plot_per_subframe(ttfaf_matrix, options.keys(), sim_params["name"], DATA_FOLDER)
    plot_cdf(ttfaf_matrix, options.keys(), sim_params["name"], DATA_FOLDER)
    print_pki(ttfaf_matrix, options.keys(), sim_params["name"], DATA_FOLDER)

    plt.show()
