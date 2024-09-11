# Copyright (C) 2024 qBraid
#
# This file is part of the qBraid-SDK
#
# The qBraid-SDK is free software released under the GNU General Public License v3
# or later. You can redistribute and/or modify it under the terms of the GPL v3.
# See the LICENSE file in the project root or <https://www.gnu.org/licenses/gpl-3.0.html>.
#
# THERE IS NO WARRANTY for the qBraid-SDK, as per Section 15 of the GPL v3.

# pylint:disable=redefined-outer-name

"""
Unit tests for Azure Quantum runtime (remote)

"""
import os
from typing import Optional

import pyqir
import pyquil
import pyquil.gates
import pytest
from azure.identity import ClientSecretCredential
from azure.quantum import Workspace
from azure.quantum._constants import ConnectionConstants, EnvironmentVariables
from azure.quantum.target.microsoft import MicrosoftEstimatorResult
from qiskit import QuantumCircuit

from qbraid.runtime import DeviceStatus, JobStatus
from qbraid.runtime.azure import AzureQuantumProvider, AzureQuantumResult
from qbraid.transpiler.conversions.qiskit import qiskit_to_pyqir


@pytest.fixture
def credential() -> Optional[ClientSecretCredential]:
    """Fixture for Azure client secret credential."""
    tenant_id = os.getenv(EnvironmentVariables.AZURE_TENANT_ID)
    client_id = os.getenv(EnvironmentVariables.AZURE_CLIENT_ID)
    client_secret = os.getenv(EnvironmentVariables.AZURE_CLIENT_SECRET)
    if client_id and tenant_id and client_secret:
        return ClientSecretCredential(
            tenant_id=tenant_id, client_id=client_id, client_secret=client_secret
        )
    return None


@pytest.fixture
def resource_id() -> Optional[str]:
    """Fixture for Azure Quantum resource ID."""
    subscription_id = os.getenv(EnvironmentVariables.QUANTUM_SUBSCRIPTION_ID)
    resource_group = os.getenv(EnvironmentVariables.QUANTUM_RESOURCE_GROUP, "AzureQuantum")
    workspace_name = os.getenv(EnvironmentVariables.WORKSPACE_NAME)
    if subscription_id and resource_group and workspace_name:
        return ConnectionConstants.VALID_RESOURCE_ID(
            subscription_id=subscription_id,
            resource_group=resource_group,
            workspace_name=workspace_name,
        )
    return None


@pytest.fixture
def workspace(
    credential: Optional[ClientSecretCredential], resource_id: Optional[str]
) -> Workspace:
    """Fixture for Azure Quantum workspace."""
    location = os.getenv(EnvironmentVariables.QUANTUM_LOCATION, "eastus")
    return Workspace(resource_id=resource_id, location=location, credential=credential)


@pytest.fixture
def provider(workspace: Workspace) -> AzureQuantumProvider:
    """Fixture for AzureQuantumProvider."""
    return AzureQuantumProvider(workspace)


@pytest.mark.remote
def test_submit_qasm2_to_quantinuum(provider: AzureQuantumProvider):
    """Test submitting an OpenQASM 2 string to run on the Quantinuum simulator."""
    device = provider.get_device("quantinuum.sim.h1-1sc")
    assert device.status() == DeviceStatus.ONLINE

    circuit = """
    OPENQASM 2.0;
    include "qelib1.inc";
    qreg q[3];
    creg c0[3];
    h q[0];
    cx q[0], q[1];
    cx q[1], q[2];
    measure q[0] -> c0[0];
    measure q[1] -> c0[1];
    measure q[2] -> c0[2];
    """

    job = device.run(circuit, shots=100)
    job.wait_for_final_state()
    assert job.status() == JobStatus.COMPLETED

    result = job.result()
    assert isinstance(result, AzureQuantumResult)
    assert result.measurement_counts() == {"000": 100}


@pytest.mark.remote
def test_submit_json_to_ionq(provider: AzureQuantumProvider):
    """Test submitting a circuit JSON to run on the IonQ simulator."""
    device = provider.get_device("ionq.simulator")
    assert device.status() == DeviceStatus.ONLINE

    circuit = {
        "qubits": 3,
        "circuit": [
            {"gate": "h", "target": 0},
            {"gate": "cnot", "control": 0, "target": 1},
            {"gate": "cnot", "control": 0, "target": 2},
        ],
    }

    job = device.run(circuit, shots=100)
    job.wait_for_final_state()
    assert job.status() == JobStatus.COMPLETED

    result = job.result()
    assert isinstance(result, AzureQuantumResult)
    assert result.measurement_counts() == {"000": 50, "111": 50}


@pytest.fixture
def qiskit_circuit() -> QuantumCircuit:
    """Fixture for a Qiskit quantum circuit."""
    circuit = QuantumCircuit(3, 3)
    circuit.name = "main"
    circuit.h(0)
    circuit.cx(0, 1)
    circuit.cx(1, 2)
    circuit.measure([0, 1, 2], [0, 1, 2])

    return circuit


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
        run_input = qir_bitcode
        device.set_options(transpile=False, transform=False, verify=False)
    else:
        run_input = qiskit_circuit

    job = device.run(run_input, input_params=input_params)

    job.wait_for_final_state()

    assert job.status() == JobStatus.COMPLETED

    result = job.result()
    assert isinstance(result, MicrosoftEstimatorResult)


@pytest.fixture
def pyquil_program() -> pyquil.Program:
    """Fixture for a PyQuil program."""
    p = pyquil.Program()
    ro = p.declare("ro", "BIT", 2)
    p += pyquil.gates.H(0)
    p += pyquil.gates.CNOT(0, 1)
    p += pyquil.gates.MEASURE(0, ro[0])
    p += pyquil.gates.MEASURE(1, ro[1])

    return p


@pytest.fixture
def quil_string(pyquil_program: pyquil.Program) -> str:
    """Fixture for a Quil string."""
    return pyquil_program.out()


@pytest.mark.remote
@pytest.mark.parametrize("direct", [(True), (False)])
def test_submit_quil_to_rigetti(
    provider: AzureQuantumProvider, pyquil_program: pyquil.Program, quil_string: str, direct: bool
):
    """Test submitting a pyQuil program or Quil string to run on the Rigetti simulator."""
    device = provider.get_device("rigetti.sim.qvm")
    assert device.status() == DeviceStatus.ONLINE

    if direct:
        run_input = quil_string
        device.set_options(transpile=False, transform=False, verify=False)
    else:
        run_input = pyquil_program

    job = device.run(run_input, shots=100, input_params={})
    job.wait_for_final_state()
    assert job.status() == JobStatus.COMPLETED

    result = job.result()
    assert isinstance(result, AzureQuantumResult)
    assert result.measurement_counts() == {"00": 60, "11": 40}
