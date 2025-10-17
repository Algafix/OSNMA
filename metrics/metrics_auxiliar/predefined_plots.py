import json
import matplotlib.pyplot as plt
import numpy as np
import numpy.typing as npt
from pathlib import Path


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


def plot_satellites_sf(tow_sf_values, name, data_folder: Path, json_status_file: str):

    with open(data_folder / json_status_file, 'r') as f:
        states_json = json.load(f)

    satellites = np.zeros(len(tow_sf_values))
    osnma_satellites = np.zeros(len(tow_sf_values))
    tags_connected = np.zeros(len(tow_sf_values))
    tags_not_connected_view = np.zeros(len(tow_sf_values))
    tags_not_connected_lost = np.zeros(len(tow_sf_values))
    sats_dict = {k: [] for k in range(40)}
    osnma_sats_dict = {k: [] for k in range(40)}

    ## Remove extra subframes and fill in gaps
    start_sf = tow_sf_values[0]
    end_sf = tow_sf_values[-1]
    previous_sf_tow = None
    curated_states_json: list[dict] = []
    for state_json in states_json:
        sf_tow = state_json['metadata']['GST_subframe'][1]
        if sf_tow < start_sf:
            continue
        elif sf_tow > end_sf:
            break
        elif state_json['metadata']['OSNMAlib_status'] != 'STARTED':
            print(f'tow with TTFAF but OSNMA not started: {sf_tow}')
            return

        if previous_sf_tow is None:
            curated_states_json.append(state_json)
        elif sf_tow == previous_sf_tow + 30:
            curated_states_json.append(state_json)
        else:
            missed_sf = (sf_tow - previous_sf_tow) // 30 - 1
            curated_states_json.extend([None]*missed_sf)
            curated_states_json.append(state_json)
        previous_sf_tow = sf_tow

    ## Extract data
    for i, tow_sf in enumerate(tow_sf_values):
        sf_state_json = curated_states_json[i]
        if sf_state_json is None:
            continue

        satellites[i] = (len(sf_state_json['nav_data_received']))
        osnma_satellites[i] = (len(sf_state_json['OSNMA_material_received']))

        for svid_s in sf_state_json['nav_data_received'].keys():
            sats_dict[int(svid_s)].append(tow_sf)
        for svid_s in sf_state_json['OSNMA_material_received'].keys():
            osnma_sats_dict[int(svid_s)].append(tow_sf)

        for svid, sat_osnma in sf_state_json['OSNMA_material_received'].items():
            for tag in sat_osnma['mack_data']['tags']:
                if tag is not None and tag[1] == 0:
                    if str(tag[0]) in sf_state_json['OSNMA_material_received']:
                        tags_connected[i] += 1
                    elif str(tag[0]) in sf_state_json['nav_data_received']:
                        tags_not_connected_view[i] += 1
                    else:
                        tags_not_connected_lost[i] += 1

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


def plot_ttfaf_sf(tow_sf_values, ttfaf_sf_matrix, options, name, data_folder: Path):

    min_sf_ttfaf_matrix = np.transpose(np.min(ttfaf_sf_matrix, axis=2))
    max_sf_ttfaf_matrix = np.transpose(np.max(ttfaf_sf_matrix, axis=2))

    fig, ax1 = plt.subplots(1, 1, figsize=(16, 9))

    for min_sf_vector, max_sf_vector, config_name in zip(min_sf_ttfaf_matrix, max_sf_ttfaf_matrix, options):
        line, = plt.plot(tow_sf_values, min_sf_vector, 'v')
        plt.plot(tow_sf_values, min_sf_vector, '-', label=config_name, color=line.get_color())

    plt.ylabel('TTFAF (s)')
    plt.xlabel('Time of Week (s)')
    plt.title(f"Minimum TTFAF per Subframe - {name}")
    plt.grid()
    #plt.legend(loc='upper right')


def plot_per_subframe(plot_ttfaf_vectors: npt.NDArray, options, name, data_folder: Path, json_status_file = 'status_log.json'):
    tow_vector = plot_ttfaf_vectors[0]
    ttfaf_matrix = plot_ttfaf_vectors[1:]

    sf_start_offset = 0 if (r := tow_vector[0] % 30) == 0 else int(30 - r)
    sf_end_offset = int(len(tow_vector) - (tow_vector[-1] + 1) % 30)
    tow_sf_values = tow_vector[sf_start_offset:sf_end_offset:30]
    ttfaf_sf_matrix = np.split(ttfaf_matrix[:, sf_start_offset:sf_end_offset], len(tow_sf_values), axis=1)

    plot_satellites_sf(tow_sf_values, name, data_folder, json_status_file)

    plot_ttfaf_sf(tow_sf_values, ttfaf_sf_matrix, options, name, data_folder)


def plot_cdf(plot_ttfaf_vectors: npt.NDArray, options, name, data_folder: Path):

    fig, ax1 = plt.subplots(1, 1, figsize=(10, 7))

    for idx, (ttfaf_vector, config_name) in enumerate(zip(plot_ttfaf_vectors[1:], options)):
        # Calculate CDF
        seconds_thr = np.arange(np.min(ttfaf_vector),np.max(ttfaf_vector)+1)
        cdf = np.array([np.sum(ttfaf_vector <= thr) for thr in seconds_thr]) / len(ttfaf_vector)*100
        plt.plot(seconds_thr, cdf, label=config_name)

    plt.tight_layout(pad=2.0)
    plt.ylabel('Percentage')
    plt.xlabel('TTFAF (s)')
    plt.title(f"Cumulative Distribution Plot (CDF) - {name}")
    plt.grid()
    plt.legend(loc='lower right')


def print_pki(plot_ttfaf_vectors: npt.NDArray, options, name, data_folder: Path):

    ttfaf_matrix = plot_ttfaf_vectors[1:]

    for ttfaf_vector, config_name in zip(ttfaf_matrix, options):
        print(f"{config_name}")
        print(f"Best:\t\t{np.min(ttfaf_vector)}")
        print(f"Average:\t{np.average(ttfaf_vector)}")
        print(f"P95:\t\t{np.percentile(ttfaf_vector, 95)}")
        print("")

def plot_ttff_vs_ttfaf(ttfaf_matrix: npt.NDArray, ttff_matrix: npt.NDArray, options, name, data_folder: Path):

    tow_vector = ttfaf_matrix[0]
    tow_sf_divisions = [t for t in tow_vector if t % 30 == 0]
    for ttfaf_vector, ttff_vector, config_name in zip(ttfaf_matrix[1:], ttff_matrix[1:], options):

        fig, ax1 = plt.subplots(1, 1, figsize=(16, 9))
        plt.plot(tow_vector, ttfaf_vector, '.', label="TTFAF")
        plt.plot(tow_vector, ttff_vector, '.', label="TTFF")
        for tow in tow_sf_divisions:
            plt.axvline(x=tow, ymin=0.01, ymax=0.99, color='r', ls='-', alpha=0.5)

        plt.ylabel('Time [s]')
        plt.title(config_name)
        plt.grid()
        plt.legend(loc='upper right')

        # Print KPIs
        print(f"{config_name}")
        print(f"\tTTFAF")
        print(f"Best:\t\t{np.min(ttfaf_vector)}")
        print(f"Average:\t{np.average(ttfaf_vector)}")
        print(f"P95:\t\t{np.percentile(ttfaf_vector, 95)}")
        print(f"\tTTFF")
        print(f"Best:\t\t{np.min(ttff_vector)}")
        print(f"Average:\t{np.average(ttff_vector)}")
        print(f"P95:\t\t{np.percentile(ttff_vector, 95)}")
        print("")
