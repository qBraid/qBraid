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
Unit tests for the qbraid visualization plot histogram function

"""

import pytest

from qbraid.visualization import plot_histogram


def test_plot_histogram_single_dict():
    counts_dict = {"00": 50, "01": 30, "10": 10, "11": 10}
    plot_histogram(counts_dict, title="Single Dict Test", show_plot=False)


def test_plot_histogram_multiple_dicts():
    counts_dict1 = {"00": 50, "01": 30, "10": 10, "11": 10}
    counts_dict2 = {"00": 20, "01": 40, "10": 30, "11": 10}

    plot_histogram(
        counts=[counts_dict1, counts_dict2],
        legend=["First Execution", "Second Execution"],
        colors=["crimson", "midnightblue"],
        title="Multiple Dicts Test",
        show_plot=False,
    )


def test_plot_histogram_mismatched_legend_length():
    counts_dict1 = {"00": 50, "01": 30, "10": 10, "11": 10}
    counts_dict2 = {"00": 20, "01": 40, "10": 30, "11": 10}

    with pytest.raises(ValueError):
        plot_histogram(
            counts=[counts_dict1, counts_dict2],
            legend=["Only one label"],
            colors=["crimson", "midnightblue"],
            show_plot=False,
        )


def test_plot_histogram_mismatched_colors_length():
    counts_dict1 = {"00": 50, "01": 30, "10": 10, "11": 10}
    counts_dict2 = {"00": 20, "01": 40, "10": 30, "11": 10}

    with pytest.raises(ValueError):
        plot_histogram(
            counts=[counts_dict1, counts_dict2],
            legend=["First Execution", "Second Execution"],
            colors=["only one color"],
            show_plot=False,
        )
