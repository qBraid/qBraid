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
Unit tests for qbraid.programs.ionq.IonQProgram

"""
import pytest

from qbraid.programs.exceptions import ProgramTypeError
from qbraid.programs.gate_model.ionq import IonQProgram
from qbraid.programs.typer import IonQDict


@pytest.fixture
def ionq_dict() -> IonQDict:
    """Return a valid IonQDict object."""
    return {
        "qubits": 3,
        "circuit": [
            {"gate": "h", "target": 0},
            {"gate": "cnot", "control": 0, "target": 1},
            {"gate": "cnot", "control": 0, "target": 2},
        ],
    }


@pytest.fixture
def ionq_program(ionq_dict: IonQDict) -> IonQProgram:
    """Return an IonQProgram object."""
    return IonQProgram(ionq_dict)


def test_ionq_program_bits(ionq_program: IonQProgram):
    """Test the qubits and clbits properties."""
    assert ionq_program.num_qubits == 3
    assert ionq_program.num_clbits == 0


def test_ionq_program_type_error():
    """Test that an error is raised when the input is not an IonQDict object."""
    invalid_program = {"qubits": 3, "circuit": 42}
    with pytest.raises(ProgramTypeError):
        IonQProgram(invalid_program)
