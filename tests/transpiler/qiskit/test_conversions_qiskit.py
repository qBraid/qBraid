# Copyright (C) 2023 qBraid
#
# This file is part of the qBraid-SDK
#
# The qBraid-SDK is free software released under the GNU General Public License v3
# or later. You can redistribute and/or modify it under the terms of the GPL v3.
# See the LICENSE file in the project root or <https://www.gnu.org/licenses/gpl-3.0.html>.
#
# THERE IS NO WARRANTY for the qBraid-SDK, as per Section 15 of the GPL v3.

"""
Unit tests for conversions between Cirq circuits and Qiskit circuits.

"""
import cirq
import numpy as np
import pytest
import qiskit

from qbraid.interface import circuits_allclose
from qbraid.transpiler.conversions.cirq import cirq_to_qasm2, qasm2_to_cirq
from qbraid.transpiler.conversions.qiskit import qiskit_to_qasm2
from qbraid.transpiler.converter import convert_to_package

from ..cirq_utils import _equal


def test_bell_state_to_from_circuits():
    """Tests cirq.Circuit --> qiskit.QuantumCircuit --> cirq.Circuit
    with a Bell state circuit.
    """
    qreg = cirq.LineQubit.range(2)
    cirq_circuit = cirq.Circuit([cirq.ops.H.on(qreg[0]), cirq.ops.CNOT.on(qreg[0], qreg[1])])
    qiskit_circuit = convert_to_package(cirq_circuit, "qiskit")  # Qiskit from Cirq
    circuit_cirq = convert_to_package(qiskit_circuit, "cirq")  # Cirq from Qiskit
    assert np.allclose(cirq_circuit.unitary(), circuit_cirq.unitary())


def test_bell_state_to_from_qasm():
    """Tests cirq.Circuit --> QASM string --> cirq.Circuit
    with a Bell state circuit.
    """
    qreg = cirq.LineQubit.range(2)
    cirq_circuit = cirq.Circuit([cirq.ops.H.on(qreg[0]), cirq.ops.CNOT.on(qreg[0], qreg[1])])
    qasm = cirq_to_qasm2(cirq_circuit)  # Qasm from Cirq
    circuit_cirq = qasm2_to_cirq(qasm)
    assert np.allclose(cirq_circuit.unitary(), circuit_cirq.unitary())


def test_random_circuit_to_from_circuits():
    """Tests cirq.Circuit --> qiskit.QuantumCircuit --> cirq.Circuit
    with a random two-qubit circuit.
    """
    cirq_circuit = cirq.testing.random_circuit(
        qubits=2, n_moments=10, op_density=0.99, random_state=1
    )
    qiskit_circuit = convert_to_package(cirq_circuit, "qiskit")
    circuit_cirq = convert_to_package(qiskit_circuit, "cirq")
    assert np.allclose(cirq_circuit.unitary(), circuit_cirq.unitary())


def test_random_circuit_to_from_qasm():
    """Tests cirq.Circuit --> QASM string --> cirq.Circuit
    with a random one-qubit circuit.
    """
    circuit_0 = cirq.testing.random_circuit(qubits=2, n_moments=10, op_density=0.99, random_state=2)
    qasm = cirq_to_qasm2(circuit_0)
    circuit_1 = qasm2_to_cirq(qasm)
    u_0 = circuit_0.unitary()
    u_1 = circuit_1.unitary()
    assert cirq.equal_up_to_global_phase(u_0, u_1)


@pytest.mark.parametrize("as_qasm", (True, False))
def test_convert_with_barrier(as_qasm):
    """Tests converting a Qiskit circuit with a barrier to a Cirq circuit."""
    n = 5
    qiskit_circuit = qiskit.QuantumCircuit(qiskit.QuantumRegister(n))
    qiskit_circuit.barrier()

    if as_qasm:
        cirq_circuit = qasm2_to_cirq(qiskit_to_qasm2(qiskit_circuit))
    else:
        cirq_circuit = convert_to_package(qiskit_circuit, "cirq")

    assert _equal(cirq_circuit, cirq.Circuit())


@pytest.mark.parametrize("as_qasm", (True, False))
def test_convert_with_multiple_barriers(as_qasm):
    """Tests converting a Qiskit circuit with barriers to a Cirq circuit."""
    n = 1
    num_ops = 10

    qreg = qiskit.QuantumRegister(n)
    qiskit_circuit = qiskit.QuantumCircuit(qreg)
    for _ in range(num_ops):
        qiskit_circuit.h(qreg)
        qiskit_circuit.barrier()

    if as_qasm:
        cirq_circuit = qasm2_to_cirq(qiskit_to_qasm2(qiskit_circuit))
    else:
        cirq_circuit = convert_to_package(qiskit_circuit, "cirq")

    qbit = cirq.LineQubit(0)
    correct = cirq.Circuit(cirq.ops.H.on(qbit) for _ in range(num_ops))
    assert _equal(cirq_circuit, correct)
    assert circuits_allclose(qiskit_circuit, cirq_circuit, strict_gphase=True)
