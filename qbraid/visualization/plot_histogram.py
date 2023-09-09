# Copyright (C) 2023 qBraid
#
# This file is part of the qBraid-SDK
#
# The qBraid-SDK is free software released under the GNU General Public License v3
# or later. You can redistribute and/or modify it under the terms of the GPL v3.
# See the LICENSE file in the project root or <https://www.gnu.org/licenses/gpl-3.0.html>.
#
# THERE IS NO WARRANTY for the qBraid-SDK, as per Section 15 of the GPL v3.

"""
Module for plotting historgram of measurement counts against quantum states.

"""

from typing import Dict, List, Optional, Union

import matplotlib.pyplot as plt
from matplotlib import colormaps

# pylint: disable=too-many-arguments


def _counts_to_decimal(counts: dict) -> dict:
    """
    Converts a dictionary of counts to decimal form.

    Args:
        counts_dict (dict): A dictionary where keys are strings representing states and
                            values are integers representing counts.

    Returns:
        dict: A dictionary with the same keys as the input dictionary, but with values
              converted to their respective decimal proportions.

    Raises:
        ValueError: If the total count is zero.
        TypeError:  If the input dictionary contains non-integer values

    Example:
        >>> counts_to_decimal({"00": 10, "01": 15, "10": 20, "11": 5})
        {"00": 0.2, "01": 0.3, "10": 0.4, "11": 0.1}
    """

    try:
        total_count = sum(counts.values())
    except TypeError as err:
        raise TypeError("Counts values must be integers.") from err

    if total_count == 0:
        raise ValueError("Total count cannot be zero.")

    decimal_dict = {key: value / total_count for key, value in counts.items()}

    return decimal_dict


def plot_histogram(
    counts: Union[List[dict], Dict],
    legend: Optional[Union[List[str], str]] = None,
    colors: Optional[Union[List[str], str]] = None,
    title: Optional[str] = None,
    x_label: Optional[str] = None,
    y_label: Optional[str] = None,
    show_plot: Optional[bool] = True,
    save_path: Optional[str] = None,
):
    """
    Plots a histogram of measurement counts against quantum states.

    Args:
        counts (Union[List[Dict], Dict]): Dictionary or a list of dictionaries containing the
                                          quantum states as keys and their respective counts as
                                          values.
        legend (Optional[Union[List[str], str]]): List of strings or a single string representing
                                                  the labels of the datasets. Defaults to None,
                                                  where it generates default labels.
        colors (Optional[Union[List[str], str]]): List of strings or a single string representing
                                                  the colors for each dataset. Defaults to None,
                                                  where it generates a color sequence.
        title (Optional[str]): String representing the title of the plot. Defaults to None.
        x_label (Optional[str]): String representing the label for the x-axis. Defaults to None.
        y_label (Optional[str]): String representing the label for the y-axis. Defaults to None.
        show_plot (Optional[bool]): Boolean representing whether to show the plot. Defaults to True.
        save_path (Optional[str]): String representing the path to save the plot. Defaults to None.

    Returns:
        None: This function does not return a value; it displays a plot.

    Raises:
        ValueError: Raises an error if input arguments do not match the expected types or formats.

    Example:
        .. code-block:: python

            counts_dict1 = {'00': 50, '01': 30, '10': 10, '11': 10}
            counts_dict2 = {'00': 20, '01': 40, '10': 30, '11': 10}

            plot_histogram(
                counts=[counts_dict1, counts_dict2],
                legend=['First Execution', 'Second Execution'],
                colors=['crimson', 'midnightblue'],
                title="Quantum State Measurements",
                x_label="Quantum States",
                y_label="Counts"
            )
    """

    if not isinstance(counts, list):
        counts = [counts]
        if isinstance(colors, str):
            colors = [colors]
        if isinstance(legend, str):
            legend = [legend]

    counts = [_counts_to_decimal(counts_dict) for counts_dict in counts]
    all_states = sorted(set(state for counts_dict in counts for state in counts_dict.keys()))

    num_dicts = len(counts)
    bar_width = 0.8 / num_dicts

    x_positions = range(len(all_states))

    if colors is None:
        cmap = colormaps.get_cmap("tab10")
        colors = [cmap(i / 10) for i in range(num_dicts)]

    if len(colors) != len(counts):
        raise ValueError("Number of colors must match number of datasets")

    if isinstance(legend, list) and len(legend) != len(counts):
        raise ValueError("Number of legend labels must match number of datasets")

    for i, counts_dict in enumerate(counts):
        counts = [counts_dict.get(state, 0) for state in all_states]

        default_label = f"Job {i}" if num_dicts > 1 else None
        label = legend[i] if legend and i < len(legend) else default_label

        plt.bar(
            [x + (i * bar_width) for x in x_positions],
            counts,
            width=bar_width,
            color=colors[i % num_dicts],
            label=label,
            align="center",
        )

    plt.xticks(x_positions, all_states, rotation=45)

    y_label = "Probabilities" if not y_label else y_label
    plt.ylabel(y_label)

    if x_label:
        plt.xlabel(x_label)

    if title:
        plt.title(title)

    if legend or num_dicts > 1:
        plt.legend()

    if save_path:
        plt.savefig(save_path)

    if show_plot:
        plt.show()
