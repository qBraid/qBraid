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
Unit tests for qbraid.programs.pytket.PytketCircuit

"""

from unittest.mock import Mock, patch

import numpy as np
import pytest
from pytket.circuit import Circuit
from pytket.unit_id import Qubit

from qbraid.programs.exceptions import ProgramTypeError, TransformError
from qbraid.programs.libs.pytket import IONQ_GATES, PytketCircuit


def test_program_attributes():
    """Test attributes of pytket circuit"""
    circuit = Circuit(2, 1)
    circuit.H(0)
    circuit.CX(0, 1)
    qprogram = PytketCircuit(circuit)
    assert qprogram.qubits == [Qubit(0), Qubit(1)]
    assert qprogram.num_qubits == 2
    assert qprogram.num_clbits == 1
    assert qprogram.depth == 2


@pytest.mark.parametrize(
    "input_circuit, expected_circuit",
    [
        (Circuit(2).CX(0, 1), Circuit(2).CX(1, 0)),
        (Circuit(3).CCX(0, 1, 2), Circuit(3).CCX(2, 1, 0)),
    ],
)
def test_reverse_qubit_order(input_circuit, expected_circuit):
    """Test reversing qubit ordering of pytket circuit."""
    qprogram = PytketCircuit(input_circuit)
    qprogram.reverse_qubit_order()
    result_circuit = qprogram.program
    assert result_circuit.get_commands() == expected_circuit.get_commands()


def test_remove_idle_qubits_pytket():
    """Test wires with no operations from pytket circuit"""
    circuit = Circuit(3)
    circuit.H(0)
    circuit.CX(0, 1)
    qprogram = PytketCircuit(circuit)
    qprogram.remove_idle_qubits()
    contig_circuit = qprogram.program
    assert contig_circuit.n_qubits == 2


@pytest.mark.parametrize("flat", [True, False])
@pytest.mark.parametrize("list_type", [True, False])
def test_gate_to_matrix_pytket(flat, list_type):
    """Test converting pytket gates to matrix"""
    c = Circuit(10, 2, name="example")
    c.CU1(np.pi / 2, 2, 3)

    c_unitary = PytketCircuit.gate_to_matrix(
        gates=c.get_commands()[0] if list_type else c.get_commands(), flat=flat
    )
    if flat:
        assert c_unitary.shape[0] == 2**2
    else:
        assert c_unitary.shape[0] == 2**4


def test_assertion_error_in_rebase():
    """Test assertion error in rebase method"""
    circuit = Circuit(1).H(0)
    gates = IONQ_GATES
    max_qubits = 5

    with patch(
        "qbraid.programs.libs.pytket.CompilationUnit.check_all_predicates", return_value=False
    ):
        with pytest.raises(TransformError) as excinfo:
            PytketCircuit.rebase(circuit, gates, max_qubits)

    assert "Rebased circuit failed to satisfy compilation predicates" in str(excinfo.value)


def test_raise_program_type_error():
    """Test raising ProgramTypeError"""
    with pytest.raises(ProgramTypeError):
        PytketCircuit(Mock())
