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
Module defining input and output data formats for Azure Quantum.

"""

from enum import Enum


class InputDataFormat(Enum):
    """Enum for defining input data formats for Azure Quantum."""

    MICROSOFT = "qir.v1"
    IONQ = "ionq.circuit.v1"
    QUANTINUUM = "honeywell.openqasm.v1"
    RIGETTI = "rigetti.quil.v1"


class OutputDataFormat(Enum):
    """Enum for defining output data formats for Azure Quantum."""

    MICROSOFT_V1 = "microsoft.quantum-results.v1"
    MICROSOFT_V2 = "microsoft.quantum-results.v2"
    IONQ = "ionq.quantum-results.v1"
    QUANTINUUM = "honeywell.quantum-results.v1"
    RESOURCE_ESTIMATOR = "microsoft.resource-estimates.v1"
    RIGETTI = "rigetti.quil-results.v1"
