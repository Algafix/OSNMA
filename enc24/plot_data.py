import json
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import numpy as np
import numpy.typing as npt
import tikzplotlib
from pathlib import Path


def plot_tags_per_sf(case):

    fig, ax1 = plt.subplots(1, 1, figsize=(10, 7))

    plt.stairs(case["cross_tags"][:-1], case["subframe_tow"], fill=True, label="All cross-auth tags")
    plt.stairs(case["cross_tags_in_view"][:-1], case["subframe_tow"], fill=True, label="Cross-auth tags for satellites in view")

    plt.ylabel('Number of tags', fontsize=14)
    plt.xlabel('Time [s]', fontsize=14)
    plt.title(f"{case['name']} - Cross-auth tags per subframe", fontsize=16)
    plt.yticks(fontsize=12)
    plt.xticks(fontsize=12)
    plt.legend(loc='upper right', fontsize=11)
    plt.tight_layout(pad=2.0)


def set_ratio_of_tags(case):
    case["ratio_all"] = np.sum(case["cross_tags_in_view"])/np.sum(case["cross_tags"])

    tags_first_subframe = np.sum([tag_num for tag_num, tow in zip(case["cross_tags"], case["subframe_tow"]) if tow % 60 == 0])
    tags_in_view_first_subframe = np.sum([tag_num for tag_num, tow in zip(case["cross_tags_in_view"], case["subframe_tow"]) if tow % 60 == 0])
    case["ratio_first_subframe"] = tags_in_view_first_subframe/tags_first_subframe

    tags_second_subframe = np.sum([tag_num for tag_num, tow in zip(case["cross_tags"], case["subframe_tow"]) if tow % 60 == 30])
    tags_in_view_second_subframe = np.sum([tag_num for tag_num, tow in zip(case["cross_tags_in_view"], case["subframe_tow"]) if tow % 60 == 30])
    case["ratio_second_subframe"] = tags_in_view_second_subframe/tags_second_subframe


def plot_tags_for_sats(cases_to_plot):

    for case in cases_to_plot:

        with open(case["file_name"], 'r') as state_file:
            osnma_state = json.load(state_file)

        subframe_tow = []
        cross_tags = []
        cross_tags_in_view = []

        for idx, subframe in enumerate(osnma_state):
            subframe_tow.append(subframe["Metadata"]["GST Subframe"][1])
            sats_in_view = [int(svid) for svid in subframe["Nav Data Received"].keys()]

            cross_tags_in_subframe = 0
            cross_tags_in_view_subframe = 0
            for svid, osnma_data in subframe["OSNMA Data"].items():
                for prn_d in [tag[0] for tag in osnma_data["Tags"] if tag is not None and tag[1] == 0 and tag[0] != int(svid)]:
                    cross_tags_in_subframe += 1
                    if prn_d in sats_in_view:
                        cross_tags_in_view_subframe += 1

            cross_tags.append(cross_tags_in_subframe)
            cross_tags_in_view.append(cross_tags_in_view_subframe)

        case["subframe_tow"] = subframe_tow
        case["cross_tags"] = cross_tags
        case["cross_tags_in_view"] = cross_tags_in_view

        plot_tags_per_sf(case)
        set_ratio_of_tags(case)

    # all cases subplot

    fig, axes_list = plt.subplots(2, 2, figsize=(16, 9))
    plt.tight_layout(pad=2.0)
    plt.subplots_adjust(hspace=0.25)

    for ax, case in zip(axes_list.ravel(), cases_to_plot):
        plt.sca(ax)
        plt.bar(["All Subframes","First Subframe","Second Subframe"],
                [case["ratio_all"], case["ratio_first_subframe"], case["ratio_second_subframe"]],
                color = ['#1f77b4', '#ff7f0e', '#2ca02c']
                )
        plt.title(f"{case['name']}", fontsize=16)
        plt.yticks(fontsize=12)
        plt.xticks(fontsize=12)
        plt.ylim(0,1)
        ax.yaxis.set_major_formatter(mtick.PercentFormatter(1.0))

        print(f"{case['name']} - Total percentage tags in view {case['ratio_all']:.02f}")
        print(f"{case['name']} - Percentage tags in view first subframe {case['ratio_first_subframe']:.02f}")
        print(f"{case['name']} - Percentage tags in view second subframe {case['ratio_second_subframe']:.02f}")

    plt.show()


if __name__ == '__main__':

    cases_to_plot = [
        {"name": "Sequence 1: First Recording",
         "file_name": "prev_config_eu_district/osnma_state_eu_short.json"},
        {"name": "Sequence 1: Second Recording",
         "file_name": "prev_config_old_town/osnma_state_old_town_short.json"},
        {"name": "Sequence 2: First Recording",
         "file_name": "current_eu_district/osnma_state_eu_district.json"},
        {"name": "Sequence 2: Second Recording",
         "file_name": "current_old_town/osnma_state_old_town.json"}
    ]

    plot_tags_for_sats(cases_to_plot)