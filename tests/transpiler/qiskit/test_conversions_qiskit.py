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
Unit tests for conversions between Cirq circuits and Qiskit circuits.

"""
import cirq
import numpy as np
import pyqasm
import pytest
import qiskit
from cirq import Circuit, LineQubit, ops, testing
from qiskit import QuantumCircuit
from qiskit.circuit.random import random_circuit

from qbraid.interface import circuits_allclose
from qbraid.programs import load_program
from qbraid.transpiler.conversions.cirq import cirq_to_qasm2
from qbraid.transpiler.conversions.qasm2 import qasm2_to_cirq
from qbraid.transpiler.conversions.qasm3 import qasm3_to_qiskit
from qbraid.transpiler.conversions.qiskit import qiskit_to_qasm2, qiskit_to_qasm3
from qbraid.transpiler.converter import transpile
from qbraid.transpiler.exceptions import ProgramConversionError

from ..cirq_utils import _equal


def test_bell_state_to_from_circuits():
    """Tests cirq.Circuit --> qiskit.QuantumCircuit --> cirq.Circuit
    with a Bell state circuit.
    """
    qreg = cirq.LineQubit.range(2)
    cirq_circuit = cirq.Circuit([cirq.ops.H.on(qreg[0]), cirq.ops.CNOT.on(qreg[0], qreg[1])])
    qiskit_circuit = transpile(cirq_circuit, "qiskit")  # Qiskit from Cirq
    circuit_cirq = transpile(qiskit_circuit, "cirq")  # Cirq from Qiskit
    assert np.allclose(cirq_circuit.unitary(), circuit_cirq.unitary())


def test_bell_state_to_qiskit():
    """Tests cirq.Circuit --> qiskit.QuantumCircuit --> cirq.Circuit
    with a Bell state circuit."""
    qreg = LineQubit.range(2)
    cirq_circuit = Circuit([ops.H.on(qreg[0]), ops.CNOT.on(qreg[0], qreg[1])])
    qiskit_circuit = transpile(cirq_circuit, "qiskit")
    assert circuits_allclose(qiskit_circuit, cirq_circuit, strict_gphase=True)


@pytest.mark.parametrize("num_qubits", [1, 2, 3, 4, 5])
def test_random_circuit_to_qiskit(num_qubits):
    """Tests converting random Cirq circuits to Qiskit circuits."""
    for _ in range(10):
        cirq_circuit = testing.random_circuit(
            qubits=num_qubits,
            n_moments=np.random.randint(1, 6),
            op_density=1,
            random_state=np.random.randint(1, 10),
        )
        qiskit_circuit = transpile(cirq_circuit, "qiskit")
        assert circuits_allclose(qiskit_circuit, cirq_circuit, strict_gphase=True)


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
    qiskit_circuit = transpile(cirq_circuit, "qiskit")
    circuit_cirq = transpile(qiskit_circuit, "cirq")
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
        cirq_circuit = transpile(qiskit_circuit, "cirq")

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
        cirq_circuit = transpile(qiskit_circuit, "cirq")

    qbit = cirq.LineQubit(0)
    correct = cirq.Circuit(cirq.ops.H.on(qbit) for _ in range(num_ops))
    assert _equal(cirq_circuit, correct)
    assert circuits_allclose(qiskit_circuit, cirq_circuit, strict_gphase=True)


def test_bell_state_from_qiskit():
    """Tests qiskit.QuantumCircuit --> cirq.Circuit
    with a Bell state circuit.
    """
    qiskit_circuit = QuantumCircuit(2)
    qiskit_circuit.h(0)
    qiskit_circuit.cx(0, 1)
    cirq_circuit = transpile(qiskit_circuit, "cirq")
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
    qiskit_circuit.sx(0)
    qiskit_circuit.iswap(2, 3)
    qiskit_circuit.swap([0, 1], [2, 3])
    qiskit_circuit.cx(0, 1)
    cirq_circuit = transpile(qiskit_circuit, "cirq")
    assert circuits_allclose(qiskit_circuit, cirq_circuit, strict_gphase=True)


@pytest.mark.skip(reason="Phase gates resulting in error")
def test_phase_gates_from_qiskit():
    """Tests converting standard gates from Qiskit to Cirq."""
    qiskit_circuit = QuantumCircuit(4)
    qiskit_circuit.p(np.pi / 8, 3)
    qiskit_circuit.sxdg(1)
    qiskit_circuit.cp(np.pi / 4, 2, 3)
    cirq_circuit = transpile(qiskit_circuit, "cirq")
    assert circuits_allclose(qiskit_circuit, cirq_circuit, strict_gphase=True)


@pytest.mark.parametrize("qubits", ([0, 1], [1, 0]))
def test_crz_gate_from_qiskit(qubits):
    """Tests converting controlled Rz gate from Qiskit to Cirq."""
    qiskit_circuit = QuantumCircuit(2)
    qiskit_circuit.crz(np.pi / 4, *qubits)
    cirq_circuit = transpile(qiskit_circuit, "cirq", require_native=True)
    assert circuits_allclose(qiskit_circuit, cirq_circuit, strict_gphase=True)


@pytest.mark.parametrize("qubits", ([0, 1], [1, 0]))
@pytest.mark.parametrize("theta", (0, np.pi, 2 * np.pi, np.pi / 2, np.pi / 4))
def test_rzz_gate_from_qiskit(qubits, theta):
    """Tests converting Rzz gate from Qiskit to Cirq."""
    qiskit_circuit = QuantumCircuit(2)
    qiskit_circuit.rzz(theta, *qubits)
    cirq_circuit = transpile(qiskit_circuit, "cirq")
    assert circuits_allclose(qiskit_circuit, cirq_circuit, strict_gphase=True)


def test_iswap_gate_from_qiskit():
    """Tests converting iSwap gate from Qiskit to Cirq."""
    qiskit_circuit = QuantumCircuit(2)
    qiskit_circuit.h([0, 1])
    qiskit_circuit.iswap(0, 1)
    cirq_circuit = transpile(qiskit_circuit, "cirq")
    assert circuits_allclose(qiskit_circuit, cirq_circuit, strict_gphase=True)


def test_qiskit_roundtrip():
    """Test converting qiskit gates that previously failed qiskit roundtrip test."""
    qiskit_circuit = QuantumCircuit(3)
    qiskit_circuit.ccz(0, 1, 2)
    qiskit_circuit.ecr(1, 2)
    qiskit_circuit.cs(2, 0)
    cirq_circuit = transpile(qiskit_circuit, "cirq", require_native=True)
    assert circuits_allclose(qiskit_circuit, cirq_circuit, strict_gphase=False)


def test_qiskit_roundtrip_noncontig():
    """Test converting gates that previously failed qiskit roundtrip test
    with non-contiguous qubits."""
    qiskit_circuit = QuantumCircuit(4)
    qiskit_circuit.ccz(0, 1, 2)
    qiskit_circuit.ecr(1, 2)
    qiskit_circuit.cs(2, 0)
    cirq_circuit = transpile(qiskit_circuit, "cirq", require_native=True)
    qprogram = load_program(cirq_circuit)
    qprogram.remove_idle_qubits()
    qiskit_contig = qprogram.program
    assert circuits_allclose(qiskit_contig, cirq_circuit, strict_gphase=False)


def test_100_random_qiskit():
    """Test converting 100 random qiskit circuits to cirq."""

    gates_to_skip = ["rxx", "rzz"]

    def _circuit_contains_invalid_gate(qiskit_circuit):
        for gate in gates_to_skip:
            if len(qiskit_circuit.get_instructions(gate)) > 0:
                return True
        return False

    def _generate_valid_qiskit_circuit():
        qiskit_circuit = random_circuit(5, 1, max_operands=4)
        while _circuit_contains_invalid_gate(qiskit_circuit):
            qiskit_circuit = random_circuit(5, 1, max_operands=4)
        return qiskit_circuit

    for _ in range(100):
        qiskit_circuit = _generate_valid_qiskit_circuit()

        cirq_circuit = transpile(qiskit_circuit, "cirq", require_native=True)
        assert circuits_allclose(
            qiskit_circuit, cirq_circuit, strict_gphase=False, index_contig=True
        )


def test_qiskit_to_from_qasm3():
    """Test converting qiskit circuit to/from OpenQASM 3.0 string"""
    circuit_in = QuantumCircuit(2)
    circuit_in.h(0)
    circuit_in.cx(0, 1)

    qasm3_str = qiskit_to_qasm3(circuit_in)
    circuit_out = qasm3_to_qiskit(qasm3_str)
    assert circuits_allclose(circuit_in, circuit_out, strict_gphase=True)


def test_raise_circuit_conversion_error():
    """Tests raising error for unsupported gates."""
    with pytest.raises(ProgramConversionError):
        probs = np.random.uniform(low=0, high=0.5)
        cirq_circuit = Circuit(ops.PhaseDampingChannel(probs).on(*LineQubit.range(1)))
        transpile(cirq_circuit, "qiskit")


def test_raise_qasm_error():
    """Test raising error for unsupported gates."""
    with pytest.raises(pyqasm.ValidationError):
        qiskit_circuit = QuantumCircuit(1)
        qiskit_circuit.delay(300, 0)
        qasm2 = qiskit_to_qasm2(qiskit_circuit)
        _ = qasm2_to_cirq(qasm2)
