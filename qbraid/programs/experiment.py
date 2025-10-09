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
Module defining the ExperimentType enumeration.

"""
from __future__ import annotations

from enum import Enum


class ExperimentType(Enum):
    """
    Enumeration for quantum experiment types.

    Attributes:
        GATE_MODEL (str): Gate-based quantum computing (e.g., OpenQASM).
        AHS (str): Analog Hamiltonian simulation.
        ANNEALING (str): Quantum annealing for optimization problems.
        PHOTONIC (str): Photonic quantum computing using photons as qubits.
        OTHER (str): Placeholder for other or unspecified quantum computing models.
    """

    GATE_MODEL = "gate_model"
    AHS = "ahs"
    ANNEALING = "annealing"
    PHOTONIC = "photonic"
    OTHER = "other"
