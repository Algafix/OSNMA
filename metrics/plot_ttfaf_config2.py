import sys
sys.path.insert(0, '..')
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import numpy.typing as npt

from osnma.input_formats.input_misc import ICDTestVectors
from metrics_auxiliar.run_and_extract import get_ttfaf_matrix

LOGS_PATH = Path(__file__).parent / 'metrics_live_recordings_logs/'
DATA_FOLDER = Path(__file__).parent / 'scenarios/configuration_2/'

sim_params = {
    "WN": 1248,
    "TOW_START": 345601,
    "TOW_STOP": 345601 + 300,
    "input_module": ICDTestVectors,
    "name": "Hot Start TTFAF - ICD Config 2",
    "numpy_file_name": DATA_FOLDER / "ttfaf_matrix_config_2.npy",
    "config_dict": {
        'logs_path': LOGS_PATH,
        'scenario_path': DATA_FOLDER / '27_JUL_2023_GST_00_00_01_fixed.csv',
        'exec_path': DATA_FOLDER,
        'pubk_name': 'OSNMA_PublicKey_2.xml',
        'kroot_name': 'OSNMA_start_KROOT.txt',
        'stop_at_faf': True,
        'log_console': False
    }
}
def plot_ttfaf(plot_ttfaf_vectors: npt.NDArray, options, name):

    tow_vector = plot_ttfaf_vectors[0]
    ttfaf_matrix = plot_ttfaf_vectors[1:]

    fig, ax1 = plt.subplots(1, 1, figsize=(16, 9))
    for idx, (ttfaf_vector, config_name) in enumerate(zip(ttfaf_matrix, options)):
        plt.plot(tow_vector, ttfaf_vector+(0.15*idx), '*', label=config_name)

    for t in tow_vector:
        if t % 30 == 0:
            plt.axvline(x=t, ymin=0.01, ymax=0.99, color='r', ls='-', alpha=0.5)

    # plt.xticks(tow_range[::2], [t % 30 for t in tow_range[::2]])
    plt.ylabel('Time [s]')
    plt.title(name)
    plt.grid()
    plt.legend(loc='upper right')
    plt.show()

if __name__ == "__main__":

    options = {
        "IOD Link and TL 30s": {'do_crc_failed_extraction': True, 'do_tesla_key_regen': True, 'TL': 30},
        "IOD Link and TL 28s": {'do_crc_failed_extraction': True, 'do_tesla_key_regen': True, 'TL': 28}
    }

    #ttfaf_matrix = get_ttfaf_matrix(sim_params, options.values(), True)
    ttfaf_matrix = np.load(sim_params["numpy_file_name"])

    plot_ttfaf(ttfaf_matrix, options.keys(), sim_params["name"])
