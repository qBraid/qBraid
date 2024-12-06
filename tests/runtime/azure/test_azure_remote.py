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
from __future__ import annotations

import os
from typing import TYPE_CHECKING

import pytest
from qbraid_core._import import LazyLoader

from qbraid.runtime import DeviceStatus, GateModelResultData, JobStatus, Result
from qbraid.runtime.azure import AzureQuantumProvider
from qbraid.transpiler.conversions.qiskit import qiskit_to_pyqir

pyquil = LazyLoader("pyquil", globals(), "pyquil")

if TYPE_CHECKING:
    import pyquil as pyquil_


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
    assert isinstance(result, Result)
    assert isinstance(result.data, GateModelResultData)
    assert result.data.get_counts() == {"000": 100}


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
    assert isinstance(result, Result)
    assert isinstance(result.data, GateModelResultData)
    assert result.data.get_counts() == {"000": 50, "111": 50}


@pytest.fixture
def pyquil_program() -> pyquil_.Program:
    """Fixture for a PyQuil program."""
    p = pyquil.Program()
    ro = p.declare("ro", "BIT", 2)
    p += pyquil.gates.H(0)
    p += pyquil.gates.CNOT(0, 1)
    p += pyquil.gates.MEASURE(0, ro[0])
    p += pyquil.gates.MEASURE(1, ro[1])

    return p


@pytest.fixture
def quil_string(pyquil_program: pyquil_.Program) -> str:
    """Fixture for a Quil string."""
    return pyquil_program.out()


@pytest.mark.remote
@pytest.mark.parametrize("direct", [(True), (False)])
def test_submit_quil_to_rigetti(
    provider: AzureQuantumProvider, pyquil_program: pyquil_.Program, quil_string: str, direct: bool
):
    """Test submitting a pyQuil program or Quil string to run on the Rigetti simulator."""
    device = provider.get_device("rigetti.sim.qvm")
    assert device.status() == DeviceStatus.ONLINE

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
