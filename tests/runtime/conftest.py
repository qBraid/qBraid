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
import numpy as np
import pytest

from qbraid.programs import NATIVE_REGISTRY


def _braket_circuit():
    """Returns low-depth, one-qubit Braket circuit to be used for testing."""
    import braket.circuits  # pylint: disable=import-outside-toplevel

    circuit = braket.circuits.Circuit()
    circuit.h(0)
    circuit.ry(0, np.pi / 2)
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
        circuits.append(_braket_circuit())
    return circuits


@pytest.fixture
def circuit(request, run_inputs):
    """Return a circuit for testing."""
    index = request.param
    return run_inputs[index]
