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
Unit tests for qbraid.programs.pyquil.PyQuilProgram

"""
import pytest

try:
    from pyquil import Program

    from qbraid.programs.exceptions import ProgramTypeError
    from qbraid.programs.gate_model.pyquil import PyQuilProgram

    pyquil_not_installed = False
except ImportError:
    pyquil_not_installed = True


pytestmark = pytest.mark.skipif(pyquil_not_installed, reason="pyquil not installed")


def test_invalid_program_type():
    """Test raising ProgramTypeError for invalid program type"""
    with pytest.raises(ProgramTypeError):
        PyQuilProgram("OPENQASM 2.0;qreg q[2];h q[0];cx q[0],q[1];")


def test_program_properties():
    """Test properties of PyQuilProgram"""
    program = PyQuilProgram(Program())
    assert program.num_clbits == 0
    assert program.depth == 0
