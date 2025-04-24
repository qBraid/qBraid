# Copyright (C) 2025 qBraid
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
from __future__ import annotations

import importlib.util
import os
from typing import TYPE_CHECKING
from unittest.mock import MagicMock, patch

import pytest
from azure.quantum import Workspace

from qbraid.runtime import (
    AhsResultData,
    AzureQuantumProvider,
    DeviceStatus,
    GateModelResultData,
    JobStatus,
    Result,
)

# Skip pyquil and/or pulser tests if not installed
pyquil_found = importlib.util.find_spec("pyquil") is not None
pulser_found = importlib.util.find_spec("pulser") is not None

if TYPE_CHECKING:
    import pulser as pulser_
    import pyquil as pyquil_


@pytest.mark.remote
def test_submit_qasm2_to_quantinuum(provider: AzureQuantumProvider):
    """Test submitting an OpenQASM 2 string to run on the Quantinuum simulator."""
    device = provider.get_device("quantinuum.sim.h1-1sc")
    status = device.status()

    if status != DeviceStatus.ONLINE:
        pytest.skip(f"{device.id} is {status.value}")

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
    assert isinstance(result, Result)
    assert isinstance(result.data, GateModelResultData)
    assert result.data.get_counts() == {"000": 100}


@pytest.mark.remote
def test_submit_json_to_ionq(provider: AzureQuantumProvider):
    """Test submitting a circuit JSON to run on the IonQ simulator."""
    device = provider.get_device("ionq.simulator")
    status = device.status()

    if status != DeviceStatus.ONLINE:
        pytest.skip(f"{device.id} is {status.value}")

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
    assert isinstance(result, Result)
    assert isinstance(result.data, GateModelResultData)
    assert result.data.get_counts() == {"000": 50, "111": 50}


@pytest.fixture
@pytest.mark.skipif(not pyquil_found, reason="pyquil not installed")
def pyquil_program() -> pyquil_.Program:
    """Fixture for a PyQuil program."""
    import pyquil

    p = pyquil.Program()
    ro = p.declare("ro", "BIT", 2)
    p += pyquil.gates.H(0)
    p += pyquil.gates.CNOT(0, 1)
    p += pyquil.gates.MEASURE(0, ro[0])
    p += pyquil.gates.MEASURE(1, ro[1])

    return p


@pytest.fixture
@pytest.mark.skipif(not pulser_found, reason="pulser not installed")
def pulser_sequence() -> pulser_.Sequence:
    """Fixture for a Pulser sequence."""
    # pylint: disable=import-outside-toplevel
    import numpy as np
    import pulser
    from pulser.waveforms import BlackmanWaveform, RampWaveform

    # pylint: enable=import-outside-toplevel

    qubits = {
        "q0": (0, 0),
        "q1": (0, 10),
        "q2": (8, 2),
        "q3": (1, 15),
        "q4": (-10, -3),
        "q5": (-8, 5),
    }
    reg = pulser.Register(qubits)

    seq = pulser.Sequence(reg, pulser.devices.DigitalAnalogDevice)
    # Declare a channel. In this example we will be using `rydberg_global`
    seq.declare_channel("ch0", "rydberg_global")
    amp_wf = BlackmanWaveform(1000, np.pi)
    det_wf = RampWaveform(1000, -5, 5)
    pulse = pulser.Pulse(amp_wf, det_wf, 0)
    seq.add(pulse, "ch0")

    return seq


@pytest.fixture
@pytest.mark.skipif(not pyquil_found, reason="pyquil not installed")
def quil_string(pyquil_program: pyquil_.Program) -> str:
    """Fixture for a Quil string."""
    return pyquil_program.out()


@pytest.mark.remote
@pytest.mark.skipif(not pyquil_found, reason="pyquil not installed")
@pytest.mark.parametrize("direct", [(True), (False)])
def test_submit_quil_to_rigetti(
    provider: AzureQuantumProvider, pyquil_program: pyquil_.Program, quil_string: str, direct: bool
):
    """Test submitting a pyQuil program or Quil string to run on the Rigetti simulator."""
    device = provider.get_device("rigetti.sim.qvm")
    status = device.status()

    if status != DeviceStatus.ONLINE:
        pytest.skip(f"{device.id} is {status.value}")

    shots = 100
    input_params = {}

    if direct:
        job = device.submit(quil_string, shots=shots, input_params=input_params)
    else:
        job = device.run(pyquil_program, shots=100, input_params=input_params)

    job.wait_for_final_state()
    assert job.status() == JobStatus.COMPLETED

    result = job.result()
    assert isinstance(result, Result)
    assert isinstance(result.data, GateModelResultData)
    assert result.data.get_counts() == {"00": 60, "11": 40}


@pytest.mark.remote
@pytest.mark.skipif(not pulser_found, reason="pulser not installed")
def test_submit_sequence_to_pasqal(
    provider: AzureQuantumProvider, pulser_sequence: pulser_.Sequence
):
    """Test submitting a Pulser sequence-builder to run on the Pulser emulator."""
    try:
        device = provider.get_device("pasqal.sim.emu-tn")
    except ValueError:
        pytest.skip("Pasqal device not available in the current workspace")

    status = device.status()

    if status != DeviceStatus.ONLINE:
        pytest.skip(f"{device.id} is {status.value}")

    shots = 100
    input_params = {}

    job = device.submit(pulser_sequence, shots=shots, input_params=input_params)

    job.wait_for_final_state()
    assert job.status() == JobStatus.COMPLETED

    result = job.result()
    assert isinstance(result, Result)
    assert isinstance(result.data, AhsResultData)
    assert result.data.get_counts() == {"00": 60, "11": 40}


@pytest.mark.remote
@pytest.mark.skipif(
    not os.getenv("AZURE_QUANTUM_CONNECTION_STRING"), reason="No connection string set"
)
def test_provider_from_env_variables():
    """Test creating a provider from environment variables."""
    provider = AzureQuantumProvider()
    assert isinstance(provider.workspace, Workspace)


def test_workspace_from_connection_string():
    """Test creating a workspace from a connection string."""
    mock_connection_string = "mock_connection_string"

    with (
        patch.dict(os.environ, {"AZURE_QUANTUM_CONNECTION_STRING": mock_connection_string}),
        patch("azure.quantum.Workspace.from_connection_string") as mock_from_connection_string,
    ):

        mock_workspace = MagicMock(spec=Workspace)
        mock_from_connection_string.return_value = mock_workspace

        provider = AzureQuantumProvider()

        mock_from_connection_string.assert_called_once_with(mock_connection_string)
        assert provider.workspace == mock_workspace
