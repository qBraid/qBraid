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
Unit tests for Azure Quantum runtime (remote) for QIR

"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from azure.quantum.target.rigetti import Result
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


@pytest.mark.remote
@pytest.mark.parametrize("direct", [(True), (False)])
def test_submit_qir_to_azure_rigetti(
    provider: AzureQuantumProvider, qiskit_circuit: QuantumCircuit, qir_bitcode: bytes, direct: bool
):
    """Test submitting Qiskit circuit or QIR bitcode to run on the Rigetti QVM simulator."""
    device = provider.get_device("rigetti.sim.qvm")
    assert device.status() == DeviceStatus.ONLINE

    input_params = {"entryPoint": qiskit_circuit.name, "arguments": [], "count": 100}

    if direct:
        job = device.submit(qir_bitcode, input_params=input_params)
    else:
        job = device.run(qiskit_circuit, input_params=input_params)

    job.wait_for_final_state()

    assert job.status() == JobStatus.COMPLETED

    result = job.result()
    assert isinstance(result, Result)
