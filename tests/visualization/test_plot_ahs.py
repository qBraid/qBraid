# Copyright (C) 2024 qBraid
#
# This file is part of the qBraid-SDK
#
# The qBraid-SDK is free software released under the GNU General Public License v3
# or later. You can redistribute and/or modify it under the terms of the GPL v3.
# See the LICENSE file in the project root or <https://www.gnu.org/licenses/gpl-3.0.html>.
#
# THERE IS NO WARRANTY for the qBraid-SDK, as per Section 15 of the GPL v3.

"""
Unit tests for AHS visualizations

"""

from unittest.mock import patch

import pytest

from qbraid.visualization.ahs import plot_atomic_register


def test_plot_with_correct_input():
    """Test the plotting function with valid input."""
    with (
        patch("matplotlib.pyplot.show") as mock_show,
        patch("matplotlib.pyplot.savefig") as mock_save,
    ):
        plot_atomic_register([(1.0, 2.0)], [True], show=True)
        mock_show.assert_called_once()
        mock_save.assert_not_called()


def test_plot_with_save_path():
    """Test if the plot is saved to the correct path when specified."""
    with patch("matplotlib.pyplot.savefig") as mock_save:
        plot_atomic_register([(1.0, 2.0)], [True], save_path="test.png", show=False)
        mock_save.assert_called_once_with("test.png")


def test_plot_without_show():
    """Test that the plot is not shown when 'show' is False."""
    with patch("matplotlib.pyplot.show") as mock_show:
        plot_atomic_register([(1.0, 2.0)], [True], show=False)
        mock_show.assert_not_called()


def test_input_length_mismatch():
    """Test handling of input length mismatch between sites and filling."""
    with pytest.raises(ValueError) as excinfo:
        plot_atomic_register([(1.0, 2.0)], [True, False])
    assert "sites and filling must be of equal length" in str(excinfo.value)


def test_custom_labels():
    """Test that custom labels are set correctly."""
    with (
        patch("matplotlib.pyplot.xlabel") as mock_xlabel,
        patch("matplotlib.pyplot.ylabel") as mock_ylabel,
        patch("matplotlib.pyplot.title") as mock_title,
    ):
        plot_atomic_register(
            [(1.0, 2.0)],
            [True],
            title="Custom Title",
            xlabel="Custom X",
            ylabel="Custom Y",
            show=False,
        )
        mock_xlabel.assert_called_once_with("Custom X", fontsize=14)
        mock_ylabel.assert_called_once_with("Custom Y", fontsize=14)
        mock_title.assert_called_once_with("Custom Title", fontsize=16)
