import json
import numpy as np
import matplotlib.pyplot as plt
import tikzplotlib

FILENAME = './24_hours_log.json'

iod_info = {svid:{'value':[], 'tows': []} for svid in np.arange(1,37)}

def tikzplotlib_fix_ncols(obj):
    """
    workaround for matplotlib 3.6 renamed legend's _ncol to _ncols, which breaks tikzplotlib
    """
    if hasattr(obj, "_ncols"):
        obj._ncol = obj._ncols
    for child in obj.get_children():
        tikzplotlib_fix_ncols(child)

def extract_data_change(file_name: str):

    with open(file_name, 'r') as file:
        status_json = json.load(file)

    total_satellite_subframes = 0
    total_subframes = 0
    subframes_without_optimization = 0

    for subframe in status_json:
        tow = subframe["metadata"]['GST_subframe'][1]
        total_subframes += 1
        satellites_in_subframe = 0
        satellites_with_iod_change = 0
        for svid, data_info in subframe["nav_data_received"].items():
            iod_block = iod_info[int(svid)]
            iod = data_info["IOD"]
            if iod is not None:
                satellites_in_subframe += 1
                total_satellite_subframes += 1
                if len(iod_block['value']) == 0 or iod != iod_block['value'][-1]:
                    iod_block['value'].append(iod)
                    iod_block['tows'].append([tow, tow+30])
                    satellites_with_iod_change += 1
                else:
                    iod_block['tows'][-1][1] = tow+30

        if satellites_in_subframe < 4 or (satellites_in_subframe - satellites_with_iod_change) < 4:
            subframes_without_optimization += 1


    print(f"Total satellite subframes: {total_satellite_subframes}")
    total_iod_changes = sum([len(iod_dict['value']) for iod_dict in iod_info.values()])
    print(f"Total changes of IOD: {total_iod_changes}")
    print(f"Subframes without change of data: {100 * (1 - total_iod_changes/total_satellite_subframes) :.2f}")

    print('===================')
    print(f"Total subframes: {total_subframes}")
    print(f"Subframes without optimization: {subframes_without_optimization}")
    print(f"Probability of no optimization on a given subframe: {100 * (1 - subframes_without_optimization/total_subframes) :.2f}")


    # Visual of IODs
    plt.figure()
    for svid, iod_data in iod_info.items():
        plt.broken_barh([(start, end-start) for start, end in iod_data['tows']], (svid-0.3, 0.6),
                        facecolors=('tab:orange', 'tab:green', 'tab:red'))
    plt.title("IOD blocks over time")
    plt.xlabel('ToW')
    plt.ylabel('SVID')
    plt.yticks(np.arange(1,37), [str(svid) for svid in np.arange(1,37)])
    plt.ylim((0, 37))
    plt.tight_layout()

    iod_durations = [end - start for iod_data in iod_info.values() for start, end in iod_data['tows']]

    # # Histogram of times
    # plt.figure()
    # values, counts = np.unique(iod_durations, return_counts=True)
    # pvalues = [str(value) for value in values]
    # plt.bar(pvalues, counts)
    # plt.title("Histogram of IOD duration")
    # plt.xlabel('ToW')
    # plt.tight_layout()


    # # Histogram of times (cap at 900s)
    # bins = np.arange(30, 930, 30)
    # clipped_iod_durations = np.clip(iod_durations, bins[0], bins[-1])
    # all_counts = np.zeros(len(bins), dtype=int)
    # values, counts = np.unique(clipped_iod_durations, return_counts=True)
    # for value, count in zip(values, counts):
    #     idx = np.where(bins == value)
    #     all_counts[idx] = count
    # labels = bins.astype(str)
    # labels[-1] += '+'
    # fig = plt.figure()
    # plt.bar(labels, all_counts)
    # plt.xticks(rotation=45)
    # plt.title("Histogram of IOD duration over 24h")
    # plt.xlabel('Seconds')
    # plt.tight_layout()
    #
    # tikzplotlib_fix_ncols(fig)
    # tikzplotlib.save(f"histogram_900s.tex")

    # Histogram of times (cap at 750s)
    bins = np.arange(30, 780, 30)
    clipped_iod_durations = np.clip(iod_durations, bins[0], bins[-1])
    all_counts = np.zeros(len(bins), dtype=int)
    values, counts = np.unique(clipped_iod_durations, return_counts=True)
    for value, count in zip(values, counts):
        idx = np.where(bins == value)
        all_counts[idx] = count
    labels = bins.astype(str)
    labels[-1] += '+'
    fig = plt.figure()
    plt.bar(labels, all_counts)
    plt.xticks(rotation=45)
    plt.title("Histogram of IOD duration over 24h")
    plt.xlabel('Seconds')
    plt.tight_layout()

    tikzplotlib_fix_ncols(fig)
    tikzplotlib.save(f"histogram_750s.tex")

    # # CDF
    # fig, ax1 = plt.subplots(1, 1, figsize=(10, 7))
    # seconds_thr = np.arange(np.min(iod_durations),np.max(iod_durations)+1)
    # cdf = np.array([np.sum(iod_durations <= thr) for thr in seconds_thr]) / len(iod_durations)*100
    # plt.plot(seconds_thr, cdf)
    # plt.ylabel('Percentage')
    # plt.xlabel('TTFAF (s)')
    # plt.title("Cumulative Distribution Plot (CDF) of the IOD duration over 24h")
    # plt.grid()
    # plt.tight_layout()

    plt.show()

if __name__ == '__main__':
    extract_data_change(FILENAME)
