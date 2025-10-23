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
    plot_runtime_conversion_scheme
    circuit_drawer
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
from .exceptions import VisualizationError
from .flair_animations import animate_qpu_state
from .plot_conversions import plot_conversion_graph, plot_runtime_conversion_scheme
from .plot_counts import plot_distribution, plot_histogram

__all__ = [
    "plot_histogram",
    "plot_distribution",
    "plot_conversion_graph",
    "plot_runtime_conversion_scheme",
    "circuit_drawer",
    "plot_atomic_register",
    "animate_qpu_state",
    "VisualizationError",
]
