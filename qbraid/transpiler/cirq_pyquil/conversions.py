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

"""
Module containing functions to convert between Cirq's circuit
representation and pyQuil's circuit representation (Quil programs).

"""
from cirq import Circuit, LineQubit
from cirq.contrib.quil_import import circuit_from_quil
from pyquil import Program

from qbraid.interface.convert_to_contiguous import convert_to_contiguous

QuilType = str


def to_quil(circuit: Circuit) -> QuilType:
    """Returns a Quil string representing the input Cirq circuit.

    Args:
        circuit: Cirq circuit to convert to a Quil string.

    Returns:
        QuilType: Quil string equivalent to the input Cirq circuit.
    """
    max_qubit = max(circuit.all_qubits())
    # if we are using LineQubits, keep the qubit labeling the same
    if isinstance(max_qubit, LineQubit):
        qubit_range = max_qubit.x + 1
        return circuit.to_quil(qubit_order=LineQubit.range(qubit_range))
    # otherwise, use the default ordering (starting from zero)
    return circuit.to_quil()


def to_pyquil(circuit: Circuit, compat=True) -> Program:
    """Returns a pyQuil Program equivalent to the input Cirq circuit.

    Args:
        circuit: Cirq circuit to convert to a pyQuil Program.

    Returns:
        pyquil.Program object equivalent to the input Cirq circuit.
    """
    if compat:
        circuit = convert_to_contiguous(circuit, rev_qubits=True)
    return Program(to_quil(circuit))


def from_pyquil(program: Program, compat=True) -> Circuit:
    """Returns a Cirq circuit equivalent to the input pyQuil Program.

    Args:
        program: PyQuil Program to convert to a Cirq circuit.

    Returns:
        Cirq circuit representation equivalent to the input pyQuil Program.
    """
    circuit = from_quil(program.out())
    if compat:
        circuit = convert_to_contiguous(circuit, rev_qubits=True)
    return circuit


def from_quil(quil: QuilType) -> Circuit:
    """Returns a Cirq circuit equivalent to the input Quil string.

    Args:
        quil: Quil string to convert to a Cirq circuit.

    Returns:
        Cirq circuit representation equivalent to the input Quil string.
    """
    return circuit_from_quil(quil)
