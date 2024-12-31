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
Unit tests for QASM transform to basic gates

"""

from unittest.mock import MagicMock

import pytest
from openqasm3 import ast
from openqasm3.parser import parse

from qbraid.passes.exceptions import CompilationError, QasmDecompositionError
from qbraid.passes.qasm.compat import normalize_qasm_gate_params
from qbraid.passes.qasm.decompose import assert_gates_in_basis, rebase
from qbraid.programs.gate_model.qasm3 import OpenQasm3Program


# move to pyqasm
@pytest.mark.parametrize(
    "original_program, expected_program",
    [
        (
            """
OPENQASM 3.0;
include "stdgates.inc";
qubit[2] q;
crx(pi) q[0], q[1];
""",
            """OPENQASM 3.0;
include "stdgates.inc";
qubit[2] q;
rz(pi / 2) q[1];
ry(pi / 2) q[1];
cx q[0], q[1];
ry(-pi / 2) q[1];
cx q[0], q[1];
rz(-pi / 2) q[1];
""",
        ),
        (
            """
OPENQASM 3.0;
include "stdgates.inc";
qubit[2] q;
cry(pi/4) q[0], q[1];
""",
            """OPENQASM 3.0;
include "stdgates.inc";
qubit[2] q;
ry(pi / 4 / 2) q[1];
cx q[0], q[1];
ry(-(pi / 4 / 2)) q[1];
cx q[0], q[1];
""",
        ),
        (
            """
OPENQASM 3.0;
include "stdgates.inc";
qubit[2] q;
crz(pi/4) q[0], q[1];
""",
            """OPENQASM 3.0;
include "stdgates.inc";
qubit[2] q;
rz(pi / 4 / 2) q[1];
cx q[0], q[1];
rz(-(pi / 4 / 2)) q[1];
cx q[0], q[1];
""",
        ),
        (
            """OPENQASM 3.0;
include "stdgates.inc";
qubit[2] q;
cy q[0], q[1];""",
            """OPENQASM 3.0;
include "stdgates.inc";
qubit[2] q;
ry(pi / 2) q[1];
cx q[0], q[1];
ry(-(pi / 2)) q[1];
cx q[0], q[1];
s q[0];
""",
        ),
        (
            """OPENQASM 3.0;
include "stdgates.inc";
qubit[2] q;
cz q[0], q[1];""",
            """OPENQASM 3.0;
include "stdgates.inc";
qubit[2] q;
rz(pi / 2) q[1];
cx q[0], q[1];
rz(-(pi / 2)) q[1];
cx q[0], q[1];
s q[0];
""",
        ),
    ],
)
def test_rebase_controlled_rotation_gates(original_program: str, expected_program: str):
    """Test conversion of QASM3 program to basis gates"""
    converted_program = rebase(original_program, {"rz", "ry", "cx", "s"})
    assert converted_program == expected_program


# move to pyqasm
def test_rebase_bad_program_raises_decomposition_error():
    """Test conversion of QASM3 program to basis gates"""
    bad_program = """
OPENQASM 3.0;
include "stdgates.inc";
qubit[2] q;
crx() q[0], q[1];
"""
    with pytest.raises(QasmDecompositionError):
        rebase(bad_program, {"rz", "ry", "cx"})


# move to pyqasm
def test_rebase_bad_program_parser_error():
    """Test conversion of QASM3 program to basis gates"""
    bad_program = """
OPENQASM 3.0;
include "stdgates.inc";
qubit[2] q;
crx :-) q[0], q[1];
"""
    with pytest.raises(ValueError, match="Invalid OpenQASM program."):
        rebase(bad_program, "any")


@pytest.fixture
def qasm_crx_program() -> str:
    """Return a QASM3 program with a CRX gate."""
    return """
OPENQASM 3.0;
include "stdgates.inc";
qubit[2] q;
crx(pi) q[0], q[1];
"""


@pytest.fixture
def qasm_crx_parsed(qasm_crx_program) -> ast.Program:
    """Return the parsed QASM3 program with a CRX gate."""
    return parse(qasm_crx_program)


@pytest.fixture
def qasm_crx_decomposed() -> str:
    """Return a QASM3 program with a CRX gate decomposed into basis gates."""
    return """
OPENQASM 3.0;
include "stdgates.inc";
qubit[2] q;
rz(pi / 2) q[1];
ry(pi / 2) q[1];
cx q[0], q[1];
ry(-pi / 2) q[1];
cx q[0], q[1];
rz(-pi / 2) q[1];
"""


# move to pyqasm
def test_rebase_raises_for_basis_gates_type_error(qasm_crx_program):
    """Test rebase raises a TypeError if basis_gates is not a set"""
    with pytest.raises(
        TypeError, match="Basis gate set must be a set of strings or a string identifier."
    ):
        rebase(qasm_crx_program, 42)


# move to pyqasm
def test_rebase_raises_for_bad_basis_gate_set_identifier(qasm_crx_program):
    """Test rebase raises a TypeError if gateset is not a set"""
    with pytest.raises(ValueError, match="Invalid basis gate set identifier."):
        rebase(qasm_crx_program, gateset="null")


# move to pyqasm
def test_assert_gates_in_basis(qasm_crx_parsed: ast.Program):
    """Test assertion that all gates are in the basis"""
    with pytest.raises(
        ValueError, match="OpenQASM program uses gate 'crx' which is not in the basis gate set."
    ):
        assert_gates_in_basis(qasm_crx_parsed, {"h"})


# move to pyqasm
def test_raise_value_error_on_empty_basis_set(qasm_crx_parsed: ast.Program):
    """Test raising a ValueError when the basis set is empty"""
    with pytest.raises(ValueError, match="Basis gate set cannot be empty."):
        rebase(qasm_crx_parsed, set())


# move to pyqasm
def test_rebase_program_already_in_basis_set(qasm_crx_program: str):
    """Test that a program already in the basis set is not modified"""
    converted_program = rebase(qasm_crx_program, {"crx"})
    assert converted_program.strip() == qasm_crx_program.strip()


# move to pyqasm
def test_rebase_raises_for_unsatisfied_predicates(qasm_crx_program: str):
    """Test that rebase raises an error if the predicates are not satisfied"""
    gateset = {"h"}

    with pytest.raises(
        CompilationError,
        match="Rebasing the specified quantum program to the provided "
        f"basis gate set {gateset} is not supported.",
    ):
        rebase(qasm_crx_program, gateset)


# move to pyqasm
def test_rebase_unsatisfied_predicates_no_check(qasm_crx_program: str):
    """Test that rebase raises an error if the predicates are not satisfied"""
    assert rebase(qasm_crx_program, {"h"}, require_predicates=False) == qasm_crx_program


# move to pyqasm
def test_rebase_over_supported_decomposition_basis_set(
    qasm_crx_program: str, qasm_crx_decomposed: str
):
    """Test rebasing over basis set that matches the gates used in supported decomposition"""
    rebased_program = rebase(qasm_crx_program, {"rz", "ry", "cx"})
    assert rebased_program.strip() == qasm_crx_decomposed.strip()


def test_transform_from_device_gateset(qasm_crx_program: str, qasm_crx_decomposed: str):
    """Test transforming a program to the basis gates of a device"""
    device = MagicMock()
    device.profile.get.return_value = {"rz", "ry", "cx"}
    program = OpenQasm3Program(qasm_crx_program)
    program.transform(device=device)
    expected = normalize_qasm_gate_params(qasm_crx_decomposed).strip()
    assert program.program == expected
