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
Helper functions for providers testing

"""
import json
import random
from datetime import time

import numpy as np
from braket.device_schema import ExecutionDay
from qiskit import QuantumCircuit
from qiskit.providers.fake_provider import GenericBackendV2
from qiskit_ibm_runtime.qiskit_runtime_service import QiskitBackendNotFoundError

from qbraid.programs import NATIVE_REGISTRY, ProgramSpec
from qbraid.runtime import DeviceType, TargetProfile
from qbraid.runtime.braket import BraketProvider
from qbraid.runtime.qiskit import QiskitBackend, QiskitRuntimeProvider

SV1_ARN = "arn:aws:braket:::device/quantum-simulator/amazon/sv1"
DM1_ARN = "arn:aws:braket:::device/quantum-simulator/amazon/dm1"
HARMONY_ARN = "arn:aws:braket:us-east-1::device/qpu/ionq/Harmony"
LUCY_ARN = "arn:aws:braket:eu-west-2::device/qpu/oqc/Lucy"


def device_wrapper_inputs(vendor: str) -> list[str]:
    """
    Returns a list of device IDs from a specified vendor, excluding certain devices.

    Args:
        vendor (str): The name of the vendor ('ibm' or 'aws').

    Returns:
        list[str]: A list of device IDs available from the given vendor, excluding specific devices.

    Raises:
        ValueError: If the vendor is not supported.
    """
    vendor_configs = {
        "ibm": {"provider": QiskitRuntimeProvider(), "skip_list": []},
        "aws": {
            "provider": BraketProvider(),
            "skip_list": [
                "arn:aws:braket:us-east-1::device/qpu/ionq/Harmony",
                "arn:aws:braket:us-east-1::device/qpu/ionq/Forte-1",
            ],
        },
    }

    # Check if vendor is supported
    config = vendor_configs.get(vendor.lower())
    if config is None:
        raise ValueError(
            f"Invalid vendor '{vendor}'. Supported vendors are: {', '.join(vendor_configs.keys())}"
        )

    # Use a list comprehension to filter devices
    return [
        device.id
        for device in config["provider"].get_devices()
        if device.id not in config["skip_list"]
    ]


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


test_circuits = []
if "cirq" in NATIVE_REGISTRY:
    test_circuits.append(cirq_circuit(meas=False))
if "qiskit" in NATIVE_REGISTRY:
    test_circuits.append(qiskit_circuit(meas=False))
if "braket" in NATIVE_REGISTRY:
    test_circuits.append(braket_circuit())


## AWS dummy fixtures
class TestAwsSession:
    """Test class for AWS session."""

    def __init__(self):
        self.region = "us-east-1"

    def get_device(self, arn):  # pylint: disable=unused-argument
        """Returns metadata for a device."""
        capabilities = {
            "action": {
                "braket.ir.openqasm.program": "literally anything",
                "paradigm": {"qubitCount": 2},
            }
        }
        cap_json = json.dumps(capabilities)
        metadata = {
            "deviceType": "SIMULATOR",
            "providerName": "Amazon Braket",
            "deviceCapabilities": cap_json,
        }

        return metadata


class ExecutionWindow:
    """Test class for execution window."""

    def __init__(self):
        self.windowStartHour = time(0)
        self.windowEndHour = time(23, 59, 59)
        self.executionDay = ExecutionDay.EVERYDAY


class Service:
    """Test class for braket device service."""

    def __init__(self):
        self.executionWindows = [ExecutionWindow()]


class TestProperties:
    """Test class for braket device properties."""

    def __init__(self):
        self.service = Service()


class TestAwsDevice:
    """Test class for braket device."""

    def __init__(self, arn, aws_session=None):
        self.arn = arn
        self.aws_session = aws_session or TestAwsSession()
        self.status = "ONLINE"
        self.properties = TestProperties()
        self.is_available = True

    @staticmethod
    def get_device_region(arn):  # pylint: disable=unused-argument
        """Returns the region of a device."""
        return "us-east-1"


## Qiskit dummy fixtures
class FakeService:
    """Fake Qiskit runtime service for testing."""

    def backend(self, backend_name, instance=None):
        """Return fake backend."""
        for backend in self.backends(instance=instance):
            if backend_name == backend.name:
                return backend
        raise QiskitBackendNotFoundError("No backend matches the criteria.")

    def backends(self, **kwargs):  # pylint: disable=unused-argument
        """Return fake Qiskit backend."""
        return [GenericBackendV2(num_qubits=5), GenericBackendV2(num_qubits=20)]

    def backend_names(self, **kwargs):
        """Return fake backend names."""
        return [backend.name for backend in self.backends(**kwargs)]

    def least_busy(self, **kwargs):
        """Return least busy backend."""
        return random.choice(self.backends(**kwargs))

    def job(self, job_id):  # pylint: disable=unused-argument
        """Return fake job."""
        return


def ibm_devices():
    """Get list of wrapped ibm backends for testing."""
    provider = QiskitRuntimeProvider()
    backends = provider.get_devices(
        filters=lambda b: b.status().status_msg == "active", operational=True
    )
    return [backend.id for backend in backends]


def fake_ibm_devices():
    """Get list of fake wrapped ibm backends for testing"""
    service = FakeService()
    backends = service.backends()
    program_spec = ProgramSpec(QuantumCircuit)
    profiles = [
        TargetProfile(backend.name, DeviceType.LOCAL_SIMULATOR, backend.num_qubits, program_spec)
        for backend in backends
    ]
    return [QiskitBackend(profile, service) for profile in profiles]
