import matplotlib.pyplot as plt
import numpy as np
import numpy.typing as npt

from run_and_extract import run_with_config

def get_ttfaf_matrix(sim_params, optimizations_list, save):

    wn = sim_params["WN"]
    tow_range = range(sim_params["TOW_START"], sim_params["TOW_STOP"])
    numpy_file_name = sim_params["numpy_file_name"] if save else "ttfaf_matrix_last_run.npy"

    ttfaf_matrix = np.zeros([len(optimizations_list), tow_range.stop-tow_range.start])
    for i, config in enumerate(optimizations_list):
        for j, tow in enumerate(tow_range):
            run_config = sim_params["config_dict"]
            run_config.update(config)
            ttfaf = run_with_config(run_config, sim_params["input_module"], start_at_gst=(wn, tow))
            ttfaf_matrix[i][j] = ttfaf
        print(ttfaf_matrix[i])

    if save:
        np.save(numpy_file_name, ttfaf_matrix)

    return ttfaf_matrix

def plot_ttfaf(plot_ttfaf_vectors: npt.NDArray, tow_range: range, options):
    fig, ax1 = plt.subplots(1, 1, figsize=(16, 9))
    for idx, (ttfaf_vector, config_name) in enumerate(zip(plot_ttfaf_vectors, options)):
        plt.plot(tow_range, ttfaf_vector+(0.15*idx), '*', label=config_name)

    plt.ylabel('Time [s]')
    plt.xticks(tow_range[::2], [t % 30 for t in tow_range[::2]])

    for t in tow_range:
        if t % 30 == 0:
            plt.axvline(x=t, ymin=0.01, ymax=0.99, color='r', ls='-', alpha=0.5)

    plt.grid()
    plt.legend(loc='upper right')
    plt.show()