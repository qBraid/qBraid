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
from datetime import time

import braket.circuits
import cirq
import numpy as np
import qiskit
from braket.device_schema import ExecutionDay

from qbraid.runtime.braket import BraketProvider
from qbraid.runtime.qiskit import QiskitRuntimeProvider

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
    circuit = braket.circuits.Circuit()
    circuit.h(0)
    circuit.ry(0, np.pi / 2)
    return circuit


def cirq_circuit(meas=True):
    """Returns Low-depth, one-qubit Cirq circuit to be used for testing.
    If ``meas=True``, applies measurement operation to end of circuit."""
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
    circuit = qiskit.QuantumCircuit(1, 1) if meas else qiskit.QuantumCircuit(1)
    circuit.h(0)
    circuit.ry(np.pi / 2, 0)
    if meas:
        circuit.measure(0, 0)
    return circuit


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

    def __init__(self, start_hour, end_hour, execution_day):
        self.windowStartHour = time(hour=start_hour)
        self.windowEndHour = time(hour=end_hour)
        self.executionDay = execution_day


class Service:
    """Test class for braket device service."""

    def __init__(self, execution_windows=None):
        self.executionWindows = execution_windows


class TestProperties:
    """Test class for braket device properties."""

    def __init__(self, execution_windows=None):
        self.service = Service(execution_windows)


class TestDevice:
    """Test class for braket device."""

    def __init__(self, arn, aws_session=None):
        self.arn = arn
        self.aws_session = aws_session or TestAwsSession()
        self.status = "ONLINE"
        execution_windows = [
            ExecutionWindow(start_hour=0, end_hour=23, execution_day=ExecutionDay.MONDAY),
            ExecutionWindow(start_hour=0, end_hour=23, execution_day=ExecutionDay.TUESDAY),
            ExecutionWindow(start_hour=0, end_hour=23, execution_day=ExecutionDay.WEDNESDAY),
            ExecutionWindow(start_hour=0, end_hour=23, execution_day=ExecutionDay.THURSDAY),
            ExecutionWindow(start_hour=0, end_hour=23, execution_day=ExecutionDay.FRIDAY),
            ExecutionWindow(start_hour=0, end_hour=23, execution_day=ExecutionDay.SATURDAY),
            ExecutionWindow(start_hour=0, end_hour=23, execution_day=ExecutionDay.SUNDAY),
        ]
        device_properties = TestProperties(execution_windows=execution_windows)
        self.properties = device_properties
        self.is_available = True

    @staticmethod
    def get_device_region(arn):  # pylint: disable=unused-argument
        """Returns the region of a device."""
        return "us-east-1"
