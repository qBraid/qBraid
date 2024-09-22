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
Module for visualizing quantum programs, experimental results,
and other associated data.

.. currentmodule:: qbraid.visualization

Functions
----------

.. autosummary::
   :toctree: ../stubs/

    plot_histogram
    plot_distribution
    plot_conversion_graph
    circuit_drawer
    qasm3_drawer
    plot_atomic_register
    animate_qpu_state

Exceptions
-----------

.. autosummary::
   :toctree: ../stubs/

    VisualizationError

"""
from .ahs import plot_atomic_register
from .draw_circuit import circuit_drawer
from .draw_qasm3 import qasm3_drawer
from .exceptions import VisualizationError
from .flair_animations import animate_qpu_state
from .plot_conversions import plot_conversion_graph
from .plot_counts import plot_distribution, plot_histogram

__all__ = [
    "plot_histogram",
    "plot_distribution",
    "plot_conversion_graph",
    "circuit_drawer",
    "qasm3_drawer",
    "plot_atomic_register",
    "animate_qpu_state",
    "VisualizationError",
]
