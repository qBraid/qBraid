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
Unit tests for Cirq quantum program methods

"""

from cirq import Circuit, GridQubit, LineQubit, X, Y, Z

from qbraid.programs.cirq import CirqCircuit


def test_contiguous_line_qubits():
    """Test convert to contiguous method for line qubits."""
    circuit = Circuit()
    circuit.append(X(LineQubit(0)))
    circuit.append(Y(LineQubit(2)))
    circuit.append(Z(LineQubit(4)))

    program = CirqCircuit(circuit)
    program._contiguous_compression()

    expected_qubits = [LineQubit(0), LineQubit(1), LineQubit(2)]
    assert set(program.qubits) == set(expected_qubits)


def test_contiguous_grid_qubits():
    """Test convert to contiguous method for grid qubits."""
    circuit = Circuit()
    circuit.append(X(GridQubit(0, 0)))
    circuit.append(Y(GridQubit(0, 2)))
    circuit.append(Z(GridQubit(0, 4)))

    program = CirqCircuit(circuit)
    program._contiguous_compression()

    expected_qubits = [GridQubit(0, 0), GridQubit(0, 1), GridQubit(0, 2)]
    assert set(program.qubits) == set(expected_qubits)


def test_mixed_qubit_types():
    """Test convert to contiguous method raises error for mixed qubit type."""
    circuit = Circuit()
    circuit.append(X(LineQubit(3)))
    circuit.append(Y(GridQubit(0, 4)))

    program = CirqCircuit(circuit)
    program._contiguous_compression()

    expected_qubits = [LineQubit(0), LineQubit(1)]
    assert set(program.qubits) == set(expected_qubits)
