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
Unit tests for converting Qiskit circuits to Cirq circuits.

"""
import numpy as np
import pytest
from qiskit import QuantumCircuit
from qiskit.circuit.random import random_circuit

from qbraid import circuit_wrapper
from qbraid.exceptions import QasmError
from qbraid.interface import circuits_allclose
from qbraid.transpiler.conversions.cirq.conversions_qasm import qasm2_to_cirq
from qbraid.transpiler.conversions.qiskit.conversions_qasm import qiskit_to_qasm2
from qbraid.transpiler.converter import convert_to_package


def test_bell_state_from_qiskit():
    """Tests qiskit.QuantumCircuit --> cirq.Circuit
    with a Bell state circuit.
    """
    qiskit_circuit = QuantumCircuit(2)
    qiskit_circuit.h(0)
    qiskit_circuit.cx(0, 1)
    cirq_circuit = convert_to_package(qiskit_circuit, "cirq")
    assert circuits_allclose(qiskit_circuit, cirq_circuit, strict_gphase=True)


def test_common_gates_from_qiskit():
    """Tests converting standard gates from Qiskit to Cirq."""
    qiskit_circuit = QuantumCircuit(4)
    qiskit_circuit.h([0, 1, 2, 3])
    qiskit_circuit.x([0, 1])
    qiskit_circuit.y(2)
    qiskit_circuit.z(3)
    qiskit_circuit.s(0)
    qiskit_circuit.sdg(1)
    qiskit_circuit.t(2)
    qiskit_circuit.tdg(3)
    qiskit_circuit.rx(np.pi / 4, 0)
    qiskit_circuit.ry(np.pi / 2, 1)
    qiskit_circuit.rz(3 * np.pi / 4, 2)
    qiskit_circuit.p(np.pi / 8, 3)
    qiskit_circuit.sx(0)
    qiskit_circuit.sxdg(1)
    qiskit_circuit.iswap(2, 3)
    qiskit_circuit.swap([0, 1], [2, 3])
    qiskit_circuit.cx(0, 1)
    qiskit_circuit.cp(np.pi / 4, 2, 3)

    cirq_circuit = convert_to_package(qiskit_circuit, "cirq")
    assert circuits_allclose(qiskit_circuit, cirq_circuit, strict_gphase=True)


@pytest.mark.parametrize("qubits", ([0, 1], [1, 0]))
def test_crz_gate_from_qiskit(qubits):
    """Tests converting controlled Rz gate from Qiskit to Cirq."""
    qiskit_circuit = QuantumCircuit(2)
    qiskit_circuit.crz(np.pi / 4, *qubits)
    cirq_circuit = convert_to_package(qiskit_circuit, "cirq")
    assert circuits_allclose(qiskit_circuit, cirq_circuit, strict_gphase=True)


@pytest.mark.parametrize("qubits", ([0, 1], [1, 0]))
@pytest.mark.parametrize("theta", (0, 2 * np.pi, np.pi / 2, np.pi / 4))
def test_rzz_gate_from_qiskit(qubits, theta):
    """Tests converting Rzz gate from Qiskit to Cirq."""
    qiskit_circuit = QuantumCircuit(2)
    qiskit_circuit.rzz(theta, *qubits)
    cirq_circuit = convert_to_package(qiskit_circuit, "cirq")
    assert circuits_allclose(qiskit_circuit, cirq_circuit, strict_gphase=True)


def test_iswap_gate_from_qiskit():
    """Tests converting iSwap gate from Qiskit to Cirq."""
    qiskit_circuit = QuantumCircuit(2)
    qiskit_circuit.h([0, 1])
    qiskit_circuit.iswap(0, 1)
    cirq_circuit = convert_to_package(qiskit_circuit, "cirq")
    assert circuits_allclose(qiskit_circuit, cirq_circuit, strict_gphase=True)


def test_qiskit_roundtrip():
    """Test converting qiskit gates that previously failed qiskit roundtrip test."""
    qiskit_circuit = QuantumCircuit(3)
    qiskit_circuit.ccz(0, 1, 2)
    qiskit_circuit.ecr(1, 2)
    qiskit_circuit.cs(2, 0)
    cirq_circuit = convert_to_package(qiskit_circuit, "cirq")
    assert circuits_allclose(qiskit_circuit, cirq_circuit, strict_gphase=False)


def test_qiskit_roundtrip_noncontig():
    """Test converting gates that previously failed qiskit roundtrip test
    with non-contiguous qubits."""
    qiskit_circuit = QuantumCircuit(4)
    qiskit_circuit.ccz(0, 1, 2)
    qiskit_circuit.ecr(1, 2)
    qiskit_circuit.cs(2, 0)
    cirq_circuit = convert_to_package(qiskit_circuit, "cirq")
    qprogram = circuit_wrapper(cirq_circuit)
    qprogram.remove_idle_qubits()
    qiskit_contig = qprogram.program
    assert circuits_allclose(qiskit_contig, cirq_circuit, strict_gphase=False)


def test_100_random_qiskit():
    """Test converting 100 random qiskit circuits to cirq."""
    for _ in range(100):
        qiskit_circuit = random_circuit(4, 1)
        cirq_circuit = convert_to_package(qiskit_circuit, "cirq")
        assert circuits_allclose(qiskit_circuit, cirq_circuit, strict_gphase=False)


def test_raise_error():
    """Test raising error for unsupported gates."""
    with pytest.raises(QasmError):
        qiskit_circuit = QuantumCircuit(1)
        qiskit_circuit.delay(300, 0)
        qasm2 = qiskit_to_qasm2(qiskit_circuit)
        _ = qasm2_to_cirq(qasm2)
