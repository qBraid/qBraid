# Copyright (C) 2024 qBraid
# Copyright (C) 2024 QuEra Computing Inc.
#
# This file is part of the qBraid-SDK
#
# The qBraid-SDK is free software released under the GNU General Public License v3
# or later. You can redistribute and/or modify it under the terms of the GPL v3.
# See the LICENSE file in the project root or <https://www.gnu.org/licenses/gpl-3.0.html>.
#
# THERE IS NO WARRANTY for the qBraid-SDK, as per Section 15 of the GPL v3.

# qbraid: skip-header

"""
Module for animating QuEra simulation results using Flair Visual.

"""
from __future__ import annotations

from typing import TYPE_CHECKING, Optional, Union

from .exceptions import VisualizationError

if TYPE_CHECKING:
    import flair_visual.animation.runtime.qpustate
    import matplotlib.animation


def animate_qpu_state(  # pylint: disable=too-many-arguments
    state: Union[flair_visual.animation.runtime.qpustate.AnimateQPUState, dict],
    dilation_rate: float = 0.05,
    fps: int = 30,
    gate_display_dilation: float = 1.0,
    save_mpeg: bool = False,
    filename: str = "vqpu_animation",
    start_block: int = 0,
    n_blocks: Optional[int] = None,
    **kwargs,
) -> matplotlib.animation.FuncAnimation:
    """Animates the QPU state.

    Args:
        state (Union[AnimateQPUState, dict]): The state of the QPU atoms to animate.
        dilation_rate (float): Conversion factor from QPU time to animation time units.
            When `dilation_rate=1.0`, 1 μs of QPU execution time corresponds to 1 second
            of animation time.
        fps (int): Frames per second. Defaults to 30.
        gate_display_dilation (float, optional): Relative dilation rate for gate events.
            Defaults to 1. Higher values will display gate events for a longer period.
        save_mpeg (bool): Whether to save the animation as an MPEG file. Defaults to False.
        filename (str): The name of the '.mpeg' file to save. Defaults to "vqpu_animation".
            Ignored if `save_mpeg` is False.
        start_block (int): The starting block for the animation. Defaults to 0.
        n_blocks (int, optional): The number of blocks to animate. Defaults to None. If None,
            all blocks after `start_block` will be animated.

    Returns:
        matplotlib.animation.FuncAnimation: The generated animation object for the QPU state.

    Raises:
        VisualizationError: If an error occurs during the animation process.
    """
    # pylint: disable=import-outside-toplevel
    from flair_visual.animation.animate import animate_qpu_state as flair_animate_qpu_state
    from flair_visual.animation.runtime.qpustate import AnimateQPUState

    # pylint: enable=import-outside-toplevel

    if isinstance(state, dict):
        state = AnimateQPUState.from_json(state)

    try:
        animation = flair_animate_qpu_state(
            state=state,
            dilation_rate=dilation_rate,
            fps=fps,
            gate_display_dilation=gate_display_dilation,
            save_mpeg=save_mpeg,
            filename=filename,
            start_block=start_block,
            n_blocks=n_blocks,
            **kwargs,
        )
    except Exception as err:  # pylint: disable=broad-exception-caught
        raise VisualizationError from err

    return animation
