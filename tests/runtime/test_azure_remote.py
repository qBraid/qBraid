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
import textwrap

import pytest
from azure.identity import ClientSecretCredential
from azure.quantum import Workspace
from azure.quantum.target.microsoft import MicrosoftEstimatorResult
from qiskit import QuantumCircuit
from qiskit_qir import to_qir_module

from qbraid.runtime import DeviceStatus, JobStatus
from qbraid.runtime.azure import AzureQuantumProvider, AzureQuantumResult

# Skip tests if Azure account auth/creds not configured
skip_remote_tests: bool = os.getenv("QBRAID_RUN_REMOTE_TESTS", "False").lower() != "true"
REASON = "QBRAID_RUN_REMOTE_TESTS not set (requires configuration of Azure Quantum Workspace)"


@pytest.fixture
def provider():
    """Fixture for AzureQuantumProvider."""

    client_id = os.getenv("AZURE_CLIENT_ID")
    tenant_id = os.getenv("AZURE_TENANT_ID")
    client_secret = os.getenv("AZURE_CLIENT_SECRET")
    resource_id = os.getenv("AZURE_RESOURCE_ID")
    location = os.getenv("AZURE_LOCATION")

    credential = ClientSecretCredential(
        tenant_id=tenant_id, client_id=client_id, client_secret=client_secret
    )
    workspace = Workspace(resource_id=resource_id, location=location, credential=credential)
    return AzureQuantumProvider(workspace)


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


def test_submit_qir_to_microsoft(provider: AzureQuantumProvider):
    """Test submitting QIR bitcode to run on the Microsoft resource estimator."""
    device = provider.get_device("microsoft.estimator")
    assert device.status() == DeviceStatus.ONLINE

    circuit = QuantumCircuit(3, 3)
    circuit.name = "main"
    circuit.h(0)
    circuit.cx(0, 1)
    circuit.cx(1, 2)
    circuit.measure([0, 1, 2], [0, 1, 2])

    program = to_qir_module(circuit, record_output=False)
    module, entrypoints = program

    entrypoint = entrypoints[0]

    input_params = {"entryPoint": entrypoint, "arguments": [], "count": 100}
    job = device.run(module.bitcode, input_params=input_params)

    job.wait_for_final_state()

    assert job.status() == JobStatus.COMPLETED

    result = job.result()
    assert isinstance(result, MicrosoftEstimatorResult)


def test_submit_quil_to_rigetti(provider: AzureQuantumProvider):
    """Test submitting a Quil string to run on the Rigetti simulator."""
    device = provider.get_device("rigetti.sim.qvm")
    assert device.status() == DeviceStatus.ONLINE

    readout = "ro"
    bell_state_quil = f"""
    DECLARE {readout} BIT[2]

    H 0
    CNOT 0 1

    MEASURE 0 {readout}[0]
    MEASURE 1 {readout}[1]
    """
    bell_state_quil = textwrap.dedent(bell_state_quil).strip()
    job = device.run(bell_state_quil, shots=100, input_params={})
    job.wait_for_final_state()
    assert job.status() == JobStatus.COMPLETED

    result = job.result()
    assert isinstance(result, AzureQuantumResult)
    assert result.measurement_counts() == {"00": 60, "11": 40}
