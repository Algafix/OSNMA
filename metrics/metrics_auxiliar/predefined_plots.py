import matplotlib.pyplot as plt
import numpy as np
import numpy.typing as npt

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

def plot_cdf(plot_ttfaf_vectors: npt.NDArray, options, name):

    fig, ax1 = plt.subplots(1, 1, figsize=(16, 9))

    for idx, (ttfaf_vector, config_name) in enumerate(zip(plot_ttfaf_vectors[1:], options)):
        seconds_thr = np.arange(np.min(ttfaf_vector),np.max(ttfaf_vector)+1)
        cdf = np.array([np.sum(ttfaf_vector <= thr) for thr in seconds_thr]) / len(ttfaf_vector)*100
        plt.plot(seconds_thr, cdf, label=config_name)

    plt.ylabel('Percentage')
    plt.xlabel('Seconds [s]')
    plt.title(name)
    plt.grid()
    plt.legend(loc='lower right')