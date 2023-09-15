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
Unit tests for PyTKET utility functions.

"""
import pytest
from pytket.circuit import Circuit

from qbraid import circuit_wrapper


@pytest.mark.parametrize(
    "input_circuit, expected_circuit",
    [
        (Circuit(2).CX(0, 1), Circuit(2).CX(1, 0)),
        (Circuit(3).CCX(0, 1, 2), Circuit(3).CCX(2, 1, 0)),
    ],
)
def test_reverse_qubit_order(input_circuit, expected_circuit):
    """Test reversing qubit ordering of pytket circuit."""
    qprogram = circuit_wrapper(input_circuit)
    qprogram.reverse_qubit_order()
    result_circuit = qprogram.program
    assert result_circuit.get_commands() == expected_circuit.get_commands()
