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
import braket.circuits
import cirq
import numpy as np
import qiskit

from qbraid.runtime.braket import BraketProvider
from qbraid.runtime.qiskit import QiskitRuntimeProvider


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
