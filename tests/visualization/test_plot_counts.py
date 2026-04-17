# Copyright 2025 qBraid
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Unit tests for the qbraid visualization plot counts functions

"""

from unittest.mock import patch

import pytest

from qbraid.visualization.plot_counts import _counts_to_decimal, plot_distribution, plot_histogram

PLOT_FNS = [plot_histogram, plot_distribution]


def test_counts_to_decimal_normal_case():
    """Test convering measurement counts to decimal probabilities."""
    counts_dict = {"00": 10, "01": 15, "10": 20, "11": 5}
    expected_output = {"00": 0.2, "01": 0.3, "10": 0.4, "11": 0.1}
    assert _counts_to_decimal(counts_dict) == expected_output


def test_counts_to_decimal_with_zero_total_count():
    """Test raising error when total of counts is zero."""
    counts_dict = {"00": 0, "01": 0, "10": 0, "11": 0}
    with pytest.raises(ValueError, match="Total count cannot be zero."):
        _counts_to_decimal(counts_dict)


def test_counts_to_decimal_with_non_integer_values():
    """Test raising error when counts values are not integers."""
    counts_dict = {"00": "ten", "01": 15, "10": 20, "11": 5}
    with pytest.raises(TypeError, match="Counts values must be integers."):
        _counts_to_decimal(counts_dict)


@pytest.mark.parametrize("plot_function", PLOT_FNS)
def test_plot_counts_single_dict(plot_function):
    """Test plotting histogram with single counts dict."""
    with (
        patch("matplotlib.pyplot.show") as mock_show,
        patch("matplotlib.pyplot.savefig") as mock_save,
    ):
        counts_dict = {"00": 50, "01": 30, "10": 10, "11": 10}
        plot_function(
            counts_dict,
            legend="Dict",
            colors="crimson",
            x_label="States",
            title="Single Dict Test",
            save_path="fake/path",
            show_plot=True,
        )
        mock_show.assert_called_once()
        mock_save.assert_called_once()

        plot_function(counts_dict)


@pytest.mark.parametrize("plot_function", PLOT_FNS)
def test_plot_histogram_multiple_dicts(plot_function):
    """Test plotting histogram with multiple counts dicts."""
    counts_dict1 = {"00": 50, "01": 30, "10": 10, "11": 10}
    counts_dict2 = {"00": 20, "01": 40, "10": 30, "11": 10}

    plot_function(
        counts=[counts_dict1, counts_dict2],
        legend=["First Execution", "Second Execution"],
        colors=["crimson", "midnightblue"],
        title="Multiple Dicts Test",
        show_plot=False,
    )


@pytest.mark.parametrize("plot_function", PLOT_FNS)
def test_plot_histogram_mismatched_legend_length(plot_function):
    """Test raising error when legend length does not match counts length."""
    counts_dict1 = {"00": 50, "01": 30, "10": 10, "11": 10}
    counts_dict2 = {"00": 20, "01": 40, "10": 30, "11": 10}

    with pytest.raises(ValueError):
        plot_function(
            counts=[counts_dict1, counts_dict2],
            legend=["Only one label"],
            colors=["crimson", "midnightblue"],
            show_plot=False,
        )


@pytest.mark.parametrize("plot_function", PLOT_FNS)
def test_plot_histogram_mismatched_colors_length(plot_function):
    """Test raising error when colors length does not match counts length."""
    counts_dict1 = {"00": 50, "01": 30, "10": 10, "11": 10}
    counts_dict2 = {"00": 20, "01": 40, "10": 30, "11": 10}

    with pytest.raises(ValueError):
        plot_function(
            counts=[counts_dict1, counts_dict2],
            legend=["First Execution", "Second Execution"],
            colors=["only one color"],
            show_plot=False,
        )
