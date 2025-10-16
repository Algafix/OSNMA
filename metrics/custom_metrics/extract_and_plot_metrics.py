from pathlib import Path
import sys
OSNMALIB_PATH = Path(__file__).resolve().parents[2]
sys.path.insert(1, str(OSNMALIB_PATH))
import matplotlib.pyplot as plt
import numpy as np

from metrics.metrics_auxiliar.run_and_extract import get_ttfaf_matrixSBF, get_kroot_and_exit, normal_run_and_exit
from metrics.metrics_auxiliar.predefined_plots import plot_ttfaf, plot_cdf, plot_per_subframe, print_pki

"""
Change DATA_FOLDER to specify where is the data
"""
DATA_FOLDER = Path('.')

"""
Dictionary with the simulation parameters for the TTFAF extraction.
 - WN : Week Number in Galileo System Time format
 - TOW_START : Time of the week at which start processing the SBF file
 - TOW_STOP : Time of the week for the last TTFAF simulation, give some minutes of margin with the end of the SBF file.
 - name : Name to display at the plots
 - numpy_file_name : Name for the file where to save the simulation results for future plotting.
 - json_status_file : [Optional] Name of the file with the json log output of the full SBF file. Needed for some plots.
 - config_dict : Normal OSNMAlib configuration dictionary. Constant for all simulation variations.
"""
sim_params = {
    "WN": 1295,
    "TOW_START": 319280,
    "TOW_STOP": 320300,
    "name": "Custom Metrics",
    "numpy_ttfaf_file_name": DATA_FOLDER / "ttfaf_matrix_custom_metrics.npy",
    "numpy_ttff_file_name": DATA_FOLDER / "ttff_matrix_custom_metrics.npy",
    "json_status_file": "example_status_log.json",
    "config_dict": {
        'scenario_path': DATA_FOLDER / 'custom_metrics.sbf',
        'exec_path': DATA_FOLDER,
        'pubk_name': 'OSNMA_PublicKey.xml',
        'kroot_name': 'OSNMA_start_KROOT.txt'
    }
}

"""
Dictionary with the OSNMAlib parameters to change on each iteration of the simulation.
Any parameter not specified is loaded with the default value.
If you are unsure of which is the default value, it is recommended to always specify it explicitly.
"""
options = {
    "IOD SotA. TL 30s": {
        'do_mack_partial_extraction': False, 'do_tesla_key_regen': False, 'do_cop_link_optimization': False,
        'do_dual_frequency': False, 'do_reed_solomon_recovery': False, 'TL': 30
    },
    "IOD SotA. Page proc. TL 25s": {
        'do_mack_partial_extraction': True, 'do_tesla_key_regen': True, 'do_cop_link_optimization': False,
        'do_dual_frequency': False, 'do_reed_solomon_recovery': False, 'TL': 25
    },
    "COP-IOD. Page proc. TL 17s": {
        'do_mack_partial_extraction': True, 'do_tesla_key_regen': True, 'do_cop_link_optimization': True,
        'do_dual_frequency': False, 'do_reed_solomon_recovery': False, 'TL': 17
    },
    "COP-IOD. Page proc. RS. TL 17s": {
        'do_mack_partial_extraction': True, 'do_tesla_key_regen': True, 'do_cop_link_optimization': True,
        'do_dual_frequency': False, 'do_reed_solomon_recovery': True, 'TL': 17
    },
    "COP-IOD. Page proc. Dual-Freq. TL 17s": {
        'do_mack_partial_extraction': True, 'do_tesla_key_regen': True, 'do_cop_link_optimization': True,
        'do_dual_frequency': True, 'do_reed_solomon_recovery': False, 'TL': 17
    },
    "COP-IOD. Page proc. Dual-Freq. RS. TL 17s": {
        'do_mack_partial_extraction': True, 'do_tesla_key_regen': True, 'do_cop_link_optimization': True,
        'do_dual_frequency': True, 'do_reed_solomon_recovery': True, 'TL': 17
    },
}


if __name__ == '__main__':

    """
    Uncomment the next line of code if you are missing the Start KROOT needed for Hot Start.
    This will run the SBF file until the first fix and output the start kroot with the name "OSNMA_start_KROOT.txt"
    """
    # get_kroot_and_exit(sim_params)

    """
    Uncomment the next line of code if you are missing the "status_log.json" file needed for some plots.
    This will run the SBF file completely and save the generated log file in this folder.
    """
    # normal_run_and_exit(sim_params, copy_json_log=True)

    """
    Run from scratch (will take a while) or load the saved matrix to just plot previous executions
    Uncomment ONLY one of them
    """
    # ttfaf_matrix = get_ttfaf_matrixSBF(sim_params, options.values(), True)
    ttfaf_matrix = np.load(sim_params["numpy_ttfaf_file_name"])

    """
    Possible plots, all of them active by default
    """
    plot_ttfaf(ttfaf_matrix, options.keys(), sim_params["name"], DATA_FOLDER)
    plot_per_subframe(ttfaf_matrix, options.keys(), sim_params["name"], DATA_FOLDER, sim_params["json_status_file"])
    plot_cdf(ttfaf_matrix, options.keys(), sim_params["name"], DATA_FOLDER)
    print_pki(ttfaf_matrix, options.keys(), sim_params["name"], DATA_FOLDER)

    plt.show()



