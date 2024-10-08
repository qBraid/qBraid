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
