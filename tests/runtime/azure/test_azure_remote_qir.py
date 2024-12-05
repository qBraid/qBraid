
"""
Unit tests for Azure Quantum runtime (remote) for QIR

"""

from __future__ import annotations
import pytest
from azure.quantum.target.microsoft import MicrosoftEstimatorResult
from qiskit import QuantumCircuit

from qbraid.runtime import DeviceStatus, JobStatus
from qbraid.runtime.azure import AzureQuantumProvider
from qbraid.transpiler.conversions.qiskit import qiskit_to_pyqir

pytest.importorskip('pyqir')
import pyqir

@pytest.fixture
def qir_bitcode(qiskit_circuit: QuantumCircuit) -> bytes:
    """Fixture for QIR bitcode from a Qiskit quantum circuit."""
    module: pyqir.Module = qiskit_to_pyqir(qiskit_circuit)
    return module.bitcode


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