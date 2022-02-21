# Copyright (C) 2020 Unitary Fund
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

"""Tests for circuit conversions."""
import cirq
import numpy as np
import pennylane as qml
import pytest
import qiskit
from braket.circuits import Circuit as BKCircuit
from braket.circuits import Instruction
from braket.circuits import gates as braket_gates
from pyquil import Program, gates

from qbraid.transpiler2._typing import SUPPORTED_PROGRAM_TYPES
from qbraid.transpiler2.interface import UnsupportedCircuitError, convert_from_cirq, convert_to_cirq
from qbraid.transpiler2.utils import _equal

# Cirq Bell circuit.
cirq_qreg = cirq.LineQubit.range(2)
cirq_qreg_rev = list(reversed(cirq_qreg))
cirq_circuit = cirq.Circuit(cirq.ops.H.on(cirq_qreg[0]), cirq.ops.CNOT.on(*cirq_qreg))
cirq_circuit_rev = cirq.Circuit(cirq.ops.H.on(cirq_qreg_rev[0]), cirq.ops.CNOT.on(*cirq_qreg_rev))

# Qiskit Bell circuit.
qiskit_qreg = qiskit.QuantumRegister(2)
qiskit_circuit = qiskit.QuantumCircuit(qiskit_qreg)
qiskit_circuit.h(qiskit_qreg[0])
qiskit_circuit.cnot(*qiskit_qreg)

# pyQuil Bell circuit.
pyquil_circuit = Program(gates.H(0), gates.CNOT(0, 1))

# Braket Bell circuit.
braket_circuit = BKCircuit(
    [
        Instruction(braket_gates.H(), 0),
        Instruction(braket_gates.CNot(), [0, 1]),
    ]
)

circuit_types = {
    "cirq": cirq.Circuit,
    "qiskit": qiskit.QuantumCircuit,
    "pyquil": Program,
    "braket": BKCircuit,
    "pennylane": qml.tape.QuantumTape,
}


@pytest.mark.parametrize("circuit", (qiskit_circuit, pyquil_circuit, braket_circuit))
def test_to_cirq(circuit):
    converted_circuit, input_type = convert_to_cirq(circuit)
    assert _equal(converted_circuit, cirq_circuit) or _equal(converted_circuit, cirq_circuit_rev)
    assert input_type in circuit.__module__


@pytest.mark.parametrize("item", ("circuit", 1, None))
def test_to_cirq_bad_types(item):
    with pytest.raises(
        UnsupportedCircuitError,
        match="Could not determine the package of the input circuit.",
    ):
        convert_to_cirq(item)


@pytest.mark.parametrize("to_type", SUPPORTED_PROGRAM_TYPES.keys())
def test_from_cirq(to_type):
    converted_circuit = convert_from_cirq(cirq_circuit, to_type)
    circuit, input_type = convert_to_cirq(converted_circuit)
    assert _equal(circuit, cirq_circuit)
    assert input_type == to_type
