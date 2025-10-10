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
Module providing interface for submitting and managing
quantum jobs through (native) qBraid APIs.

.. currentmodule:: qbraid.runtime.native

Classes
--------

.. autosummary::
   :toctree: ../stubs/

    Session
    QbraidSession
    QbraidClient
    QbraidProvider
    QbraidDevice
    QbraidJob
    QirRunner

ResultData Subclasses
^^^^^^^^^^^^^^^^^^^^^^^

.. autosummary::
   :toctree: ../stubs/

    QuEraQasmSimulatorResultData
    QbraidQirSimulatorResultData
    NECVectorAnnealerResultData
    Equal1SimulatorResultData

"""
from qbraid_core import QbraidClient, QbraidSession, Session
from qbraid_core.services.quantum.runner import QirRunner

from .device import QbraidDevice
from .job import QbraidJob
from .provider import QbraidProvider
from .result import (
    Equal1SimulatorResultData,
    NECVectorAnnealerResultData,
    QbraidQirSimulatorResultData,
    QuEraQasmSimulatorResultData,
)

__all__ = [
    "Session",
    "QbraidSession",
    "QbraidClient",
    "QbraidProvider",
    "QbraidDevice",
    "QbraidJob",
    "QirRunner",
    "QuEraQasmSimulatorResultData",
    "QbraidQirSimulatorResultData",
    "NECVectorAnnealerResultData",
    "Equal1SimulatorResultData",
]
