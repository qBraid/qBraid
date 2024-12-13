# Copyright (C) 2024 qBraid
#
# This file is part of the qBraid-SDK
#
# The qBraid-SDK is free software released under the GNU General Public License v3
# or later. You can redistribute and/or modify it under the terms of the GPL v3.
# See the LICENSE file in the project root or <https://www.gnu.org/licenses/gpl-3.0.html>.
#
# THERE IS NO WARRANTY for the qBraid-SDK, as per Section 15 of the GPL v3.

# pylint: disable=redefined-outer-name

"""
Unit tests for qbraid.programs.qasm.OpenQasm2Program

"""
import textwrap
from unittest.mock import MagicMock

import openqasm3.ast
import pytest
from openqasm3.parser import parse

from qbraid.programs.exceptions import ProgramTypeError
from qbraid.programs.gate_model.qasm2 import OpenQasm2Program
from qbraid.programs.loader import load_program
from qbraid.programs.registry import unregister_program_type
from qbraid.programs.typer import Qasm2String

from ..fixtures.qasm2.circuits import qasm2_bell, qasm2_shared15


def test_qasm_qubits():
    """Test getting QASM qubits"""
    program1 = OpenQasm2Program(qasm2_bell())
    program1.validate()
    assert program1.qubits == {"q": 2}

    program2 = OpenQasm2Program(qasm2_shared15())
    program2.validate()
    assert program2.qubits == {"q": 4}


def test_qasm_num_qubits():
    """Test calculating number of qubits in qasm2 circuit"""
    assert OpenQasm2Program(qasm2_bell()).num_qubits == 2
    assert OpenQasm2Program(qasm2_shared15()).num_qubits == 4


def test_qasm_num_clbits():
    """Test calculating number of classical bits in qasm2 circuit"""
    assert OpenQasm2Program(qasm2_shared15()).num_clbits == 4


def test_qasm_depth():
    """Test calculating depth of qasm2 circuit"""
    assert OpenQasm2Program(qasm2_bell()).depth == 2
    assert OpenQasm2Program(qasm2_shared15()).depth == 12


def test_raise_program_type_error():
    """Test raising ProgramTypeError"""
    try:
        with pytest.raises(ProgramTypeError):
            OpenQasm2Program({})
    finally:
        unregister_program_type("dict")


@pytest.fixture
def simple_qasm():
    """Fixture for a simple qasm2 circuit with measurements"""
    qasm = """
    OPENQASM 2.0;
    include "qelib1.inc";

    qreg q[2];
    creg c[2];

    h q[0];

    measure q[0] -> c[0];
    measure q[1] -> c[1];
    """
    qasm = textwrap.dedent(qasm).strip()
    return qasm


def test_num_classical_bits(simple_qasm):
    """Test calculating number of classical bits in qasm2 circuit"""

    assert OpenQasm2Program(simple_qasm).num_clbits == 2


def test_remove_measurements_via_transform(simple_qasm):
    """Test removing measurements via transform method"""
    device = MagicMock()
    device.id = "quera_qasm_simulator"
    qprogram = OpenQasm2Program(simple_qasm)
    qprogram.transform(device=device)
    assert qprogram._module.has_measurements() is False
    assert isinstance(qprogram.program, Qasm2String)


def test_load_qasm2_program_from_parsed_obj(simple_qasm):
    """Test loading a qasm2 program from a openqasm3.ast.Program object"""
    parsed_program = parse(simple_qasm)
    assert isinstance(parsed_program, openqasm3.ast.Program)

    qbraid_program = load_program(parsed_program)
    assert isinstance(qbraid_program, OpenQasm2Program)
