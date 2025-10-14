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
Unit tests for Azure Quantum runtime (remote) for QIR

"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from azure.quantum.target.microsoft import MicrosoftEstimatorResult
from qiskit import QuantumCircuit

from qbraid.runtime import DeviceStatus, JobStatus
from qbraid.runtime.azure import AzureQuantumProvider
from qbraid.transpiler.conversions.qiskit import qiskit_to_pyqir

if TYPE_CHECKING:
    import pyqir as pyqir_

pyqir = pytest.importorskip("pyqir")


@pytest.fixture
def qir_bitcode(qiskit_circuit: QuantumCircuit) -> bytes:
    """Fixture for QIR bitcode from a Qiskit quantum circuit."""
    module: pyqir_.Module = qiskit_to_pyqir(qiskit_circuit)
    return module.bitcode


@pytest.mark.skip(
    reason="The Resource Estimator is now fully open source and available as part of the QDK."
)
@pytest.mark.remote
@pytest.mark.parametrize("direct", [(True), (False)])
def test_submit_qir_to_microsoft(
    provider: AzureQuantumProvider, qiskit_circuit: QuantumCircuit, qir_bitcode: bytes, direct: bool
):
    """Test submitting Qiskit circuit or QIR bitcode to run on the Microsoft resource estimator."""
    device = provider.get_device("microsoft.estimator")
    assert device.status() == DeviceStatus.ONLINE

    input_params = {"entryPoint": qiskit_circuit.name, "arguments": [], "count": 100}

    if direct:
        job = device.submit(qir_bitcode, input_params=input_params)
    else:
        job = device.run(qiskit_circuit, input_params=input_params)

    job.wait_for_final_state()

    assert job.status() == JobStatus.COMPLETED

    result = job.result()
    assert isinstance(result, MicrosoftEstimatorResult)
