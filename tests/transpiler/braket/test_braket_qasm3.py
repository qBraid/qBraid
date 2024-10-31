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
Unit tests for converting Braket circuits to/from OpenQASM

"""
import textwrap

import numpy as np
import qiskit
from braket.circuits import Circuit

from qbraid.interface import circuits_allclose
from qbraid.transpiler.conversions.braket import braket_to_qasm3
from qbraid.transpiler.conversions.qasm3 import qasm3_to_braket
from qbraid.transpiler.conversions.qiskit import qiskit_to_qasm3


def test_braket_to_qasm3_bell_circuit():
    """Test converting braket bell circuit to OpenQASM 3.0 string"""
    qasm_expected = """
    OPENQASM 3.0;
    bit[2] b;
    qubit[2] q;
    h q[0];
    cnot q[0], q[1];
    b[0] = measure q[0];
    b[1] = measure q[1];
    """

    qasm_expected_2 = """
    OPENQASM 3.0;
    bit[2] __bits__;
    qubit[2] __qubits__;
    h __qubits__[0];
    cnot __qubits__[0], __qubits__[1];
    __bits__[0] = measure __qubits__[0];
    __bits__[1] = measure __qubits__[1];
    """
    bell = Circuit().h(0).cnot(0, 1).measure(0).measure(1)
    qasm_out = braket_to_qasm3(bell).strip()
    qasm_expected = textwrap.dedent(qasm_expected).strip()
    qasm_expected_2 = textwrap.dedent(qasm_expected_2).strip()
    assert qasm_out in [qasm_expected, qasm_expected_2]


def test_braket_to_qasm3_bell_no_measurements():
    """Test converting braket circuit with no measurements to OpenQASM 3.0 string"""
    qasm_expected = """
    OPENQASM 3.0;
    bit[2] b;
    qubit[2] q;
    h q[0];
    cnot q[0], q[1];
    """

    qasm_expected_2 = """
    OPENQASM 3.0;
    bit[2] __bits__;
    qubit[2] __qubits__;
    h __qubits__[0];
    cnot __qubits__[0], __qubits__[1];
    """
    bell = Circuit().h(0).cnot(0, 1)
    qasm_out: str = braket_to_qasm3(bell).strip()
    qasm_expected = textwrap.dedent(qasm_expected).strip()
    qasm_expected_2 = textwrap.dedent(qasm_expected_2).strip()
    assert qasm_out in [qasm_expected, qasm_expected_2]


def test_braket_from_qasm3():
    """Test converting OpenQASM 3 string to braket circuit"""
    qasm = """
    OPENQASM 3.0;
    bit[2] b;
    qubit[2] q;
    rx(0.15) q[0];
    rx(0.3) q[1];
    """
    qasm = textwrap.dedent(qasm).strip()
    circuit_expected = Circuit().rx(0, 0.15).rx(1, 0.3)
    assert circuit_expected == qasm3_to_braket(qasm)


def test_qiskit_to_qasm3_to_braket():
    """Test converting Qiskit circuit to Braket via OpenQASM 3.0 for mapped gate defs"""
    qc = qiskit.QuantumCircuit(4)
    qc.cx(0, 1)
    qc.s(0)
    qc.sdg(1)
    qc.t(2)
    qc.tdg(3)
    qc.sx(0)
    qc.sxdg(1)
    qc.p(np.pi / 8, 3)
    qc.cp(np.pi / 4, 2, 3)

    qasm3_str = qiskit_to_qasm3(qc)
    circuit = qasm3_to_braket(qasm3_str)
    assert circuits_allclose(qc, circuit)
