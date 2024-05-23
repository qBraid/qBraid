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
Unit tests for OQCProvider class

"""
import random
import time

from unittest.mock import Mock, patch

import numpy as np
import pytest

from qbraid.programs import NATIVE_REGISTRY, ProgramSpec
from qbraid.runtime import DeviceType, JobStateError, TargetProfile
from qbraid.runtime.oqc import OQCProvider, OQCDevice, OQCJob

from qcaas_client.client import OQCClient, QPUTask



def braket_circuit():
    """Returns low-depth, one-qubit Braket circuit to be used for testing."""
    import braket.circuits  # pylint: disable=import-outside-toplevel

    circuit = braket.circuits.Circuit()
    circuit.h(0)
    circuit.ry(0, np.pi / 2)
    return circuit


def cirq_circuit(meas=True):
    """Returns Low-depth, one-qubit Cirq circuit to be used for testing.
    If ``meas=True``, applies measurement operation to end of circuit."""
    import cirq  # pylint: disable=import-outside-toplevel

    q0 = cirq.GridQubit(0, 0)

    def basic_circuit():
        yield cirq.H(q0)
        yield cirq.Ry(rads=np.pi / 2)(q0)
        if meas:
            yield cirq.measure(q0, key="q0")

    circuit = cirq.Circuit()
    circuit.append(basic_circuit())
    return circuit


def qiskit_circuit(meas=True):
    """Returns Low-depth, one-qubit Qiskit circuit to be used for testing.
    If ``meas=True``, applies measurement operation to end of circuit."""
    import qiskit  # pylint: disable=import-outside-toplevel

    circuit = qiskit.QuantumCircuit(1, 1) if meas else qiskit.QuantumCircuit(1)
    circuit.h(0)
    circuit.ry(np.pi / 2, 0)
    if meas:
        circuit.measure(0, 0)
    return circuit

def test_circuits():
    """Returns list of test circuits for each available native provider."""
    circuits = []
    if "cirq" in NATIVE_REGISTRY:
        circuits.append(cirq_circuit(meas=False))
    if "qiskit" in NATIVE_REGISTRY:
        circuits.append(qiskit_circuit(meas=False))
    if "braket" in NATIVE_REGISTRY:
        circuits.append(braket_circuit())
    return circuits

device_id = "qpu:uk:2:d865b5a184"

def test_oqc_provider_device():
    with patch("qbraid.runtime.oqc.provider.OQCClient") as mock_client:
        mock_client.return_value = Mock(spec=OQCClient)
        provider = OQCProvider(api_key="fake_api_key")
        assert isinstance(provider, OQCProvider)
        assert isinstance(provider.client, OQCClient)
        assert provider.client == mock_client.return_value
        test_device = provider.get_device(device_id)
        assert isinstance(test_device, OQCDevice)
        assert test_device.profile["device_id"] == device_id
    
def test_build_runtime_profile():
    with patch("qbraid.runtime.oqc.provider.OQCClient") as mock_client:
        mock_client.return_value = Mock(spec=OQCClient)
        provider = OQCProvider(api_key="fake_api_key")
        profile = provider._build_profile({"id": device_id, "num_qubits": 8})
        assert isinstance(profile, TargetProfile)
        assert profile._data["device_id"] == device_id
        assert profile._data["device_type"] == DeviceType.SIMULATOR
        assert profile._data["num_qubits"] == 8
        assert profile._data["program_spec"] == ProgramSpec(str, alias="qasm2")
    
def test_retrieving_job():
    pass