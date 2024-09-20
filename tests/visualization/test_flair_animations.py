# Copyright (C) 2024 qBraid
#
# This file is part of the qBraid-SDK
#
# The qBraid-SDK is free software released under the GNU General Public License v3
# or later. You can redistribute and/or modify it under the terms of the GPL v3.
# See the LICENSE file in the project root or <https://www.gnu.org/licenses/gpl-3.0.html>.
#
# THERE IS NO WARRANTY for the qBraid-SDK, as per Section 15 of the GPL v3.

# pylint: disable=redefined-outer-name

"""
Unit tests for matplotlib animations using Flair Visual

"""
import logging
from unittest.mock import MagicMock, patch

import pytest

from qbraid.visualization.exceptions import VisualizationError
from qbraid.visualization.flair_animations import animate_qpu_state

try:
    from flair_visual.animation.runtime.qpustate import AnimateQPUState

    flair_visual_installed = True
except ImportError as err:
    flair_visual_installed = False

    logging.warning("flair_animations tests will be skipped: %s", err)

pytestmark = pytest.mark.skipif(
    flair_visual_installed is False, reason="flair-visual not installed"
)


@pytest.fixture
def mock_state():
    """Fixture for an empty mock AnimateQPUState object."""
    return AnimateQPUState()


@pytest.fixture
def mock_state_from_json():
    """Fixture for a mock AnimateQPUState created from JSON."""
    state_data = {
        "block_durations": [],
        "gate_events": [],
        "qpu_fov": {"xmin": None, "xmax": None, "ymin": None, "ymax": None},
        "atoms": [],
        "slm_zone": [],
        "aod_moves": [],
    }
    return AnimateQPUState.from_json(state_data)


@patch("flair_visual.animation.animate.animate_qpu_state")
def test_animate_qpu_state_with_animate_qpustate(mock_animate_qpu_state, mock_state):
    """Test the animate_qpu_state function with an AnimateQPUState object."""
    mock_animation = MagicMock()
    mock_animate_qpu_state.return_value = mock_animation

    result = animate_qpu_state(state=mock_state, dilation_rate=0.1, fps=24, save_mpeg=False)

    mock_animate_qpu_state.assert_called_once_with(
        state=mock_state,
        dilation_rate=0.1,
        fps=24,
        gate_display_dilation=1.0,
        save_mpeg=False,
        filename="vqpu_animation",
        start_block=0,
        n_blocks=None,
    )

    assert result == mock_animation


@patch("flair_visual.animation.animate.animate_qpu_state")
def test_animate_qpu_state_with_json(mock_animate_qpu_state, mock_state_from_json):
    """Test the animate_qpu_state function with a JSON dict input."""
    mock_animation = MagicMock()
    mock_animate_qpu_state.return_value = mock_animation

    state_data = {
        "block_durations": [],
        "gate_events": [],
        "qpu_fov": {"xmin": None, "xmax": None, "ymin": None, "ymax": None},
        "atoms": [],
        "slm_zone": [],
        "aod_moves": [],
    }
    result = animate_qpu_state(
        state=state_data, dilation_rate=0.1, fps=24, save_mpeg=True, filename="test_animation"
    )

    mock_animate_qpu_state.assert_called_once_with(
        state=mock_state_from_json,
        dilation_rate=0.1,
        fps=24,
        gate_display_dilation=1.0,
        save_mpeg=True,
        filename="test_animation",
        start_block=0,
        n_blocks=None,
    )
    assert result == mock_animation


@patch("flair_visual.animation.animate.animate_qpu_state")
def test_animate_qpu_state_raises_visualization_error(mock_animate_qpu_state, mock_state):
    """Test that a VisualizationError is raised when an exception occurs."""
    mock_animate_qpu_state.side_effect = ValueError("Test error")

    with pytest.raises(VisualizationError):
        animate_qpu_state(state=mock_state)


@patch("flair_visual.animation.animate.animate_qpu_state")
def test_animate_qpu_state_with_extra_kwargs(mock_animate_qpu_state, mock_state):
    """Test the animate_qpu_state function with additional kwargs."""
    mock_animation = MagicMock()
    mock_animate_qpu_state.return_value = mock_animation

    result = animate_qpu_state(state=mock_state, dilation_rate=0.2, fps=60, extra_arg=True)

    mock_animate_qpu_state.assert_called_once_with(
        state=mock_state,
        dilation_rate=0.2,
        fps=60,
        gate_display_dilation=1.0,
        save_mpeg=False,
        filename="vqpu_animation",
        start_block=0,
        n_blocks=None,
        extra_arg=True,
    )
    assert result == mock_animation
