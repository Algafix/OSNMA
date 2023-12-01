import sys
sys.path.insert(0, '..')
import matplotlib.pyplot as plt
import numpy as np

from simulate_and_plot import get_ttfaf_matrix, plot_ttfaf
import configs

def get_matrix_and_plot(sim_params, options_dict, save):
    ttfaf_matrix = get_ttfaf_matrix(sim_params, options_dict.values(), save)
    plot_ttfaf(ttfaf_matrix, range(sim_params["TOW_START"], sim_params["TOW_STOP"]), options_dict.keys())

def manual_read_and_plot(sim_params, options_names):
    ttfaf_matrix = np.load(sim_params["numpy_file_name"])
    tow_range = range(sim_params["TOW_START"], sim_params["TOW_STOP"])

    fig, ax1 = plt.subplots(1, 1, figsize=(16, 9))
    for idx, (ttfaf_vector, config_name) in enumerate(zip(ttfaf_matrix, options_names[:-1])):
        plt.plot(tow_range, ttfaf_vector+(0.15*idx), '.', label=config_name)

    plt.ylabel('Time [s]')
    plt.xticks(tow_range[::2], [t % 30 for t in tow_range[::2]])

    for t in tow_range:
        if t % 30 == 0:
            plt.axvline(x=t, ymin=0.01, ymax=0.99, color='r', ls='-', alpha=0.5)

    plt.grid()
    plt.legend(loc='upper right')
    plt.show()

if __name__ == "__main__":

    options_hot_start = {
        "base": {'do_crc_failed_extraction': False, 'do_tesla_key_regen': False},
        "crc_extraction": {'do_crc_failed_extraction': True, 'do_tesla_key_regen': False},
        "crc_and_tesla_extraction": {'do_crc_failed_extraction': True, 'do_tesla_key_regen': True}
    }

    options = {
        "TL_30": {'do_crc_failed_extraction': True, 'do_tesla_key_regen': True, 'TL': 30},
        "TL_28": {'do_crc_failed_extraction': True, 'do_tesla_key_regen': True, 'TL': 28},
        "TL_1": {'do_crc_failed_extraction': True, 'do_tesla_key_regen': True, 'TL': 1}
    }

    #ttfaf_matrix = get_ttfaf_matrix(configs.config_2_sim_params, options.values(), True)

    manual_read_and_plot(configs.config_2_sim_params, list(options.keys()))
