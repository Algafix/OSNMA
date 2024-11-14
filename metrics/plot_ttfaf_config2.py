import sys
sys.path.insert(0, '..')
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from osnma.input_formats.input_misc import ICDTestVectors
from metrics_auxiliar.run_and_extract import get_ttfaf_matrix, normal_run_and_exit
from metrics_auxiliar.predefined_plots import plot_ttfaf, plot_cdf, plot_per_subframe, print_pki

DATA_FOLDER = Path(__file__).parent / 'scenarios/configuration_2/'

sim_params = {
    "WN": 1248,
    "TOW_START": 345601,
    "TOW_STOP": 345601 + 1800,
    "input_module": ICDTestVectors,
    "name": "Hot Start TTFAF - ICD Config 2",
    "numpy_file_name": DATA_FOLDER / "ttfaf_matrix_config_2_COP.npy",
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

    #normal_run_and_exit(sim_params, test_vectors=True)

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

    ttfaf_matrix = get_ttfaf_matrix(sim_params, options.values(), True)
    #ttfaf_matrix = np.load(sim_params["numpy_file_name"])

    plot_ttfaf(ttfaf_matrix, options.keys(), sim_params["name"], DATA_FOLDER)
    plot_per_subframe(ttfaf_matrix, options.keys(), sim_params["name"], DATA_FOLDER)
    plot_cdf(ttfaf_matrix, options.keys(), sim_params["name"], DATA_FOLDER)
    print_pki(ttfaf_matrix, options.keys(), sim_params["name"], DATA_FOLDER)

    plt.show()

