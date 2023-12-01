from pathlib import Path

from osnma.input_formats.input_misc import ICDTestVectors
from osnma.input_formats.input_sbf import SBF

LOGS_PATH = Path(__file__).parent / 'metrics_live_recordings_logs/'

config_2_sim_params = {
    "WN": 1248,
    "TOW_START": 345601,
    "TOW_STOP": 345601 + 300,
    "input_module": ICDTestVectors,
    "numpy_file_name": "ttfaf_matrix_config_2.npy",
    "config_dict": {
        'logs_path': LOGS_PATH,
        'scenario_path': Path(__file__).parent / 'scenarios/configuration_2/27_JUL_2023_GST_00_00_01_fixed.csv',
        'exec_path': Path(__file__).parent / 'scenarios/configuration_2/',
        'pubk_name': 'OSNMA_PublicKey_2.xml',
        'kroot_name': 'OSNMA_start_KROOT.txt',
        'stop_at_faf': True,
        'log_console': False
    }
}