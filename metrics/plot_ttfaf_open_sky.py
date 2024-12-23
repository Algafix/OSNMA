import sys
sys.path.insert(0, '..')
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from metrics_auxiliar.run_and_extract import get_ttfaf_matrixSBF, normal_run_and_exit
from metrics_auxiliar.predefined_plots import plot_ttfaf, plot_cdf, plot_per_subframe, print_pki

DATA_FOLDER = Path(__file__).parent / 'scenarios/open_sky/'
# 2293 313200 -> 20/12/2023 - 14:00:00 UTC

sim_params = {
    "WN": 1269,
    "TOW_START": 313200,
    "TOW_STOP": 313200 + 3600,
    "name": "Hot Start TTFAF - Open Sky",
    "numpy_file_name": DATA_FOLDER / "ttfaf_matrix_open_sky_COP.npy",
    "config_dict": {
        'scenario_path': DATA_FOLDER / 'open_sky_inav.sbf',
        'exec_path': DATA_FOLDER,
        'pubk_name': 'OSNMA_PublicKey_2.xml',
        'kroot_name': 'OSNMA_start_KROOT.txt',
        'stop_at_faf': True,
        'log_console': False,
        'log_file': False
    }
}

if __name__ == "__main__":

    #normal_run_and_exit(sim_params)

    options = {
        "IOD SotA. TL 30s": {'do_mack_partial_extraction': False, 'do_tesla_key_regen': False,
                                       'do_cop_link_optimization': False, 'TL': 30},
        "COP-IOD. Page proc. TL 17s": {'do_mack_partial_extraction': True, 'do_tesla_key_regen': True,
                                       'do_cop_link_optimization': True, 'TL': 17},
        "COP-IOD. Page proc. RS. TL 17s": {'do_mack_partial_extraction': True, 'do_tesla_key_regen': True,
                                           'do_cop_link_optimization': True, 'do_dual_frequency': False,
                                           'do_reed_solomon_recovery': True, 'TL': 17},
        "COP-IOD. Page proc. Dual-Freq. TL 17s": {'do_mack_partial_extraction': True, 'do_tesla_key_regen': True,
                                                  'do_cop_link_optimization': True, 'do_dual_frequency': True,
                                                  'do_reed_solomon_recovery': False, 'TL': 17},
        "COP-IOD. Page proc. Dual-Freq. RS. TL 17s": {'do_mack_partial_extraction': True, 'do_tesla_key_regen': True,
                                                      'do_cop_link_optimization': True, 'do_dual_frequency': True,
                                                      'do_reed_solomon_recovery': True, 'TL': 17},
    }

    # Rerun from scratch (will take a while) or load the saved matrix
    #ttfaf_matrix = get_ttfaf_matrixSBF(sim_params, options.values(), True)
    ttfaf_matrix = np.load(sim_params["numpy_file_name"])

    plot_ttfaf(ttfaf_matrix, options.keys(), sim_params["name"], DATA_FOLDER)
    plot_per_subframe(ttfaf_matrix, options.keys(), sim_params["name"], DATA_FOLDER)
    plot_cdf(ttfaf_matrix, options.keys(), sim_params["name"], DATA_FOLDER)
    print_pki(ttfaf_matrix, options.keys(), sim_params["name"], DATA_FOLDER)

    plt.show()

