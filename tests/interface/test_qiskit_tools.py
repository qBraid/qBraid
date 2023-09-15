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
Unit tests for Qiskit utility functions.

"""

from qiskit import QuantumCircuit

from qbraid import circuit_wrapper


def test_reverse_qubit_order():
    """Test reversing ordering of qubits in qiskit circuit"""
    circ = QuantumCircuit(3)
    circ.h(0)
    circ.cx(0, 2)

    qprogram = circuit_wrapper(circ)
    qprogram.reverse_qubit_order()
    reversed_circ = qprogram.program

    expected_circ = QuantumCircuit(3)
    expected_circ.h(2)
    expected_circ.cx(2, 0)

    assert (
        reversed_circ == expected_circ
    ), "The reversed circuit does not match the expected output."
