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
Module defining input and output data formats for Azure Quantum.

"""

from enum import Enum


class InputDataFormat(Enum):
    """Enum for defining input data formats for Azure Quantum."""

    MICROSOFT = "qir.v1"
    IONQ = "ionq.circuit.v1"
    QUANTINUUM = "honeywell.openqasm.v1"
    RIGETTI = "rigetti.quil.v1"
    PASQAL = "pasqal.pulser.v1"


class OutputDataFormat(Enum):
    """Enum for defining output data formats for Azure Quantum."""

    MICROSOFT_V1 = "microsoft.quantum-results.v1"
    MICROSOFT_V2 = "microsoft.quantum-results.v2"
    IONQ = "ionq.quantum-results.v1"
    QUANTINUUM = "honeywell.quantum-results.v1"
    RESOURCE_ESTIMATOR = "microsoft.resource-estimates.v1"
    RIGETTI = "rigetti.quil-results.v1"
    PASQAL = "pasqal.pulser-results.v1"
