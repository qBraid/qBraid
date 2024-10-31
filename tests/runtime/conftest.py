# Copyright (C) 2024 qBraid
#
# This file is part of the qBraid-SDK
#
# The qBraid-SDK is free software released under the GNU General Public License v3
# or later. You can redistribute and/or modify it under the terms of the GPL v3.
# See the LICENSE file in the project root or <https://www.gnu.org/licenses/gpl-3.0.html>.
#
# THERE IS NO WARRANTY for the qBraid-SDK, as per Section 15 of the GPL v3.

# pylint: disable=redefined-outer-name

"""
Fixtures imported/defined in this file can be used by any test in this directory
without needing to import them (pytest will automatically discover them).

"""
import random
import textwrap
from typing import Optional

import numpy as np
import pytest

from qbraid.programs import NATIVE_REGISTRY

from ._resources import DEVICE_DATA_AQUILA, DEVICE_DATA_QIR, DEVICE_DATA_QUERA


def _braket_circuit(meas=True):
    """Returns low-depth, one-qubit Braket circuit to be used for testing."""
    import braket.circuits  # pylint: disable=import-outside-toplevel

    circuit = braket.circuits.Circuit()
    circuit.h(0)
    circuit.ry(0, np.pi / 2)
    if meas:
        circuit.measure(0)
    return circuit


def _cirq_circuit(meas=True):
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


def _qiskit_circuit(meas=True):
    """Returns Low-depth, one-qubit Qiskit circuit to be used for testing.
    If ``meas=True``, applies measurement operation to end of circuit."""
    import qiskit  # pylint: disable=import-outside-toplevel

    circuit = qiskit.QuantumCircuit(1, 1) if meas else qiskit.QuantumCircuit(1)
    circuit.h(0)
    circuit.ry(np.pi / 2, 0)
    if meas:
        circuit.measure(0, 0)
    return circuit


@pytest.fixture
def braket_circuit():
    """Returns low-depth, one-qubit Braket circuit to be used for testing."""
    return _braket_circuit()


@pytest.fixture
def qiskit_circuit():
    """Returns low-depth, one-qubit Qiskit circuit to be used for testing."""
    return _qiskit_circuit()


@pytest.fixture
def run_inputs():
    """Returns list of test circuits for each available native provider."""
    circuits = []
    if "cirq" in NATIVE_REGISTRY:
        circuits.append(_cirq_circuit(meas=False))
    if "qiskit" in NATIVE_REGISTRY:
        circuits.append(_qiskit_circuit(meas=False))
    if "braket" in NATIVE_REGISTRY:
        circuits.append(_braket_circuit(meas=False))
    return circuits


@pytest.fixture
def circuit(request, run_inputs):
    """Return a circuit for testing."""
    index = request.param
    return run_inputs[index]


@pytest.fixture
def device_data_qir():
    """Return a dictionary of device data for the qBraid QIR simulator."""
    return DEVICE_DATA_QIR


@pytest.fixture
def device_data_quera():
    """Return a dictionary of device data for the QuEra QASM simulator."""
    return DEVICE_DATA_QUERA


@pytest.fixture
def device_data_aquila():
    """Return a dictionary of device data for the QuEra Aquila QPU."""
    return DEVICE_DATA_AQUILA


@pytest.fixture
def valid_qasm2_no_meas() -> str:
    """Returns a valid qasm string."""
    qasm = """
    OPENQASM 2.0;
    include "qelib1.inc";
    qreg q[2];
    h q[0];
    cx q[0],q[1];
    cx q[1],q[0];
    """
    return textwrap.dedent(qasm).strip()


def uniform_state_circuit(num_qubits: Optional[int] = None, measure: Optional[bool] = True):
    """
    Creates a Cirq circuit where all qubits are entangled to uniformly be in
    either |0⟩ or |1⟩ states upon measurement.

    This circuit initializes the first qubit in a superposition state using a
    Hadamard gate and then entangles all other qubits to this first qubit using
    CNOT gates. This ensures all qubits collapse to the same state upon measurement,
    resulting in either all |0⟩s or all |1⟩s uniformly across different executions.

    Args:
        num_qubits (optional, int): The number of qubits in the circuit. If not provided,
                                    a default random number between 10 and 20 is used.
        measure (optional, bool): Whether to measure the qubits at the end of the circuit.

    Returns:
        cirq.Circuit: The resulting circuit where the measurement outcome of all qubits is
                      either all |0⟩s or all |1⟩s.

    Raises:
        ValueError: If the number of qubits provided is less than 1.
    """
    import cirq  # pylint: disable=import-outside-toplevel

    if num_qubits is not None and num_qubits < 1:
        raise ValueError("Number of qubits must be at least 1.")

    num_qubits = num_qubits or random.randint(10, 20)

    qubits = [cirq.LineQubit(i) for i in range(num_qubits)]

    circuit = cirq.Circuit()

    circuit.append(cirq.H(qubits[0]))

    for qubit in qubits[1:]:
        circuit.append(cirq.CNOT(qubits[0], qubit))

    if measure:
        circuit.append(cirq.measure(*qubits, key="result"))

    return circuit


@pytest.fixture
def cirq_uniform():
    """Cirq circuit used for testing."""
    return uniform_state_circuit
