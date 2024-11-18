import json
import matplotlib.pyplot as plt
import numpy as np
import numpy.typing as npt
import tikzplotlib
from pathlib import Path

def tikzplotlib_fix_ncols(obj):
    """
    workaround for matplotlib 3.6 renamed legend's _ncol to _ncols, which breaks tikzplotlib
    """
    if hasattr(obj, "_ncols"):
        obj._ncol = obj._ncols
    for child in obj.get_children():
        tikzplotlib_fix_ncols(child)


def plot_ttfaf(plot_ttfaf_vectors: npt.NDArray, options, name, data_folder: Path):

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

    tikzplotlib_fix_ncols(fig)
    Path(f"{data_folder}/tikz_plots/").mkdir(parents=True, exist_ok=True)
    tikzplotlib.save(f"{data_folder}/tikz_plots/{data_folder.name}_time.tex")


def plot_satellites_sf(tow_sf_values, name, data_folder: Path):

    with open(data_folder / 'status_log.json', 'r') as f:
        states_json = json.load(f)

    satellites = []
    osnma_satellites = []
    tags_connected = []
    tags_not_connected_view = []
    tags_not_connected_lost = []
    sats_dict = {k: [] for k in range(40)}
    osnma_sats_dict = {k: [] for k in range(40)}

    #### Get data from json ####

    for idx, sf_state_json in enumerate(states_json):
        sf_tow = sf_state_json['metadata']['GST_subframe'][1]
        sf_osnma_status = sf_state_json['metadata']['OSNMAlib_status']
        if sf_tow < tow_sf_values[0]:
            continue
        elif sf_tow > tow_sf_values[-1]:
            break
        elif sf_osnma_status != 'STARTED':
            print(f'tow with TTFAF but OSNMA not started: {sf_tow}')
            return
        satellites.append(len(sf_state_json['nav_data_received']))
        osnma_satellites.append(len(sf_state_json['OSNMA_material_received']))

        for svid_s in sf_state_json['nav_data_received'].keys():
            sats_dict[int(svid_s)].append(sf_tow)
        for svid_s in sf_state_json['OSNMA_material_received'].keys():
            osnma_sats_dict[int(svid_s)].append(sf_tow)

        tags_connected.append(0)
        tags_not_connected_view.append(0)
        tags_not_connected_lost.append(0)
        for svid, sat_osnma in sf_state_json['OSNMA_material_received'].items():
            for tag in sat_osnma['mack_data']['tags']:
                if tag is not None and tag[1] == 0:
                    if str(tag[0]) in sf_state_json['OSNMA_material_received']:
                        tags_connected[-1] += 1
                    elif str(tag[0]) in sf_state_json['nav_data_received']:
                        tags_not_connected_view[-1] += 1
                    else:
                        tags_not_connected_lost[-1] += 1

    #### Plots ####

    ### scenario sats ###
    fig, ax1 = plt.subplots(1, 1, figsize=(16, 9))
    sat_tick_map = {}
    i = 0
    for svid in sats_dict.keys():
        if len(tow_list := sats_dict[svid]) > 0:
            sat_tick_map[i] = svid
            plt.plot(tow_list, np.repeat(i, len(tow_list)), '.', color='darkorange')
            if len(tow_list := osnma_sats_dict[svid]) > 0:
                plt.plot(tow_list, np.repeat(i, len(tow_list)), 'gv')
            i += 1

    plt.plot([], [], '.', label='Tracked', color='orange')
    plt.plot([], [], 'gv', label='OSNMA connected')
    plt.title(f"Satellite status - {name}")
    plt.xlabel('Time of Week (s)')
    plt.grid()
    plt.yticks(list(sat_tick_map.keys()), list(sat_tick_map.values()))
    plt.ylabel('SVID')
    plt.legend(loc='upper right')

    tikzplotlib_fix_ncols(fig)
    Path(f"{data_folder}/tikz_plots/").mkdir(parents=True, exist_ok=True)
    tikzplotlib.save(f"{data_folder}/tikz_plots/{data_folder.name}_satellites_scenario.tex")


    ### sf sats info ###
    fig, ax1 = plt.subplots(1, 1, figsize=(16, 9))

    #ax1.plot(tow_sf_values, satellites, 'k*-', linewidth=0.5, label='Tracked')
    ax1.plot(tow_sf_values, osnma_satellites, 'gv-', linewidth=0.5, label='Connected')
    ax1.plot(tow_sf_values, [s - os for s,os in zip(satellites, osnma_satellites)], 'bv-', linewidth=0.5, label='Disconnected')
    ax1.set_ylabel('Number of Galileo Satellites')
    plt.title(f"Satellites tracked and ADKD0 tags received - {name}")
    plt.xlabel('Time of Week (s)')
    ax1.grid()
    ax1.legend(loc='upper left')

    ax2 = ax1.twinx()
    ax2.plot(tow_sf_values, tags_connected, 'g', label='Connected')
    ax2.plot(tow_sf_values, tags_not_connected_view, 'b', label='Disconnected')
    #ax2.plot(tow_sf_values, tags_not_connected_lost, 'r', label='Not OSNMA connected and not in view')
    ax2.set_ylabel('Number of tags received')
    ax2.legend(loc='upper right')

    # Common yticks
    max_value = np.max(np.concatenate((ax1.get_yticks(), ax2.get_yticks()))) + 2
    ax1.set_ylim(0, max_value)
    ax2.set_ylim(0, max_value)

    tikzplotlib_fix_ncols(fig)
    Path(f"{data_folder}/tikz_plots/").mkdir(parents=True, exist_ok=True)
    tikzplotlib.save(f"{data_folder}/tikz_plots/{data_folder.name}_satellites_sf.tex")


def plot_ttfaf_sf(tow_sf_values, ttfaf_sf_matrix, options, name, data_folder: Path):

    min_sf_ttfaf_matrix = np.transpose(np.min(ttfaf_sf_matrix, axis=2))
    max_sf_ttfaf_matrix = np.transpose(np.max(ttfaf_sf_matrix, axis=2))

    fig, ax1 = plt.subplots(1, 1, figsize=(16, 9))

    for min_sf_vector, max_sf_vector, config_name in zip(min_sf_ttfaf_matrix, max_sf_ttfaf_matrix, options):
        color = next(ax1._get_lines.prop_cycler)['color']
        plt.plot(tow_sf_values, min_sf_vector, 'v', color=color)
        plt.plot(tow_sf_values, min_sf_vector, '-', label=config_name, color=color)

    plt.ylabel('TTFAF (s)')
    plt.xlabel('Time of Week (s)')
    plt.title(f"Minimum TTFAF per Subframe - {name}")
    plt.grid()
    #plt.legend(loc='upper right')

    tikzplotlib_fix_ncols(fig)
    Path(f"{data_folder}/tikz_plots/").mkdir(parents=True, exist_ok=True)
    tikzplotlib.save(f"{data_folder}/tikz_plots/{data_folder.name}_ttfaf_sf.tex")


def plot_per_subframe(plot_ttfaf_vectors: npt.NDArray, options, name, data_folder: Path):
    tow_vector = plot_ttfaf_vectors[0]
    ttfaf_matrix = plot_ttfaf_vectors[1:]

    sf_start_offset = 0 if (r := tow_vector[0] % 30) == 0 else int(30 - r)
    sf_end_offset = int(len(tow_vector) - (tow_vector[-1] + 1) % 30)
    tow_sf_values = tow_vector[sf_start_offset:sf_end_offset:30]
    ttfaf_sf_matrix = np.split(ttfaf_matrix[:, sf_start_offset:sf_end_offset], len(tow_sf_values), axis=1)

    plot_satellites_sf(tow_sf_values, name, data_folder)

    plot_ttfaf_sf(tow_sf_values, ttfaf_sf_matrix, options, name, data_folder)


def plot_cdf(plot_ttfaf_vectors: npt.NDArray, options, name, data_folder: Path):

    fig, ax1 = plt.subplots(1, 1, figsize=(10, 7))

    for idx, (ttfaf_vector, config_name) in enumerate(zip(plot_ttfaf_vectors[1:], options)):
        # Calculate CDF
        seconds_thr = np.arange(np.min(ttfaf_vector),np.max(ttfaf_vector)+1)
        cdf = np.array([np.sum(ttfaf_vector <= thr) for thr in seconds_thr]) / len(ttfaf_vector)*100

        # Plots
        # if config_name == "IOD data link and Page level processing":
        #     plt.plot(seconds_thr, cdf, linestyle='dotted', label=config_name, lw=3)
        # elif config_name == "IOD data link and Page level processing - TL 27s":
        #     plt.plot(seconds_thr, cdf, linestyle='--', label=config_name, alpha=0.7, lw=3)
        # elif config_name == "IOD data link and Page level processing - TL 25s":
        #     plt.plot(seconds_thr, cdf, linestyle='dotted', label=config_name, lw=3)
        # else:
        #     plt.plot(seconds_thr, cdf, label=config_name, lw=3, alpha=0.5)

        plt.plot(seconds_thr, cdf, label=config_name)

    plt.tight_layout(pad=2.0)
    plt.ylabel('Percentage')
    plt.xlabel('TTFAF (s)')
    plt.title(f"Cumulative Distribution Plot (CDF) - {name}")
    plt.grid()
    plt.legend(loc='upper left', bbox_to_anchor=(0, 1))

    tikzplotlib_fix_ncols(fig)
    Path(f"{data_folder}/tikz_plots/").mkdir(parents=True, exist_ok=True)
    tikzplotlib.save(f"{data_folder}/tikz_plots/{data_folder.name}_cdf.tex")


def print_pki(plot_ttfaf_vectors: npt.NDArray, options, name, data_folder: Path):

    ttfaf_matrix = plot_ttfaf_vectors[1:]

    for ttfaf_vector, config_name in zip(ttfaf_matrix, options):
        print(f"{config_name}")
        print(f"Best:\t\t{np.min(ttfaf_vector)}")
        print(f"Average:\t{np.average(ttfaf_vector)}")
        print(f"P95:\t\t{np.percentile(ttfaf_vector, 95)}")
        print("")
