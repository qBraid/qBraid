# Copyright (C) 2025 qBraid
#
# This file is part of the qBraid-SDK
#
# The qBraid-SDK is free software released under the GNU General Public License v3
# or later. You can redistribute and/or modify it under the terms of the GPL v3.
# See the LICENSE file in the project root or <https://www.gnu.org/licenses/gpl-3.0.html>.
#
# THERE IS NO WARRANTY for the qBraid-SDK, as per Section 15 of the GPL v3.

"""
Tests for the CUDAQ program type.

"""

import pytest

try:
    from qbraid import load_program, transpile
    from qbraid.programs.exceptions import ProgramTypeError
    from qbraid.programs.gate_model.cudaq import CudaQKernel
    from qbraid.programs.registry import unregister_program_type

    cudaq_not_installed = False
except ImportError:
    cudaq_not_installed = True

pytestmark = pytest.mark.skipif(cudaq_not_installed, reason="cudaq not installed")


def test_invalid_program_initialization():
    """Tests that initializing a program with an invalid input raises a ProgramTypeError."""
    try:
        with pytest.raises(ProgramTypeError):
            CudaQKernel(("invalid", "program"))
    finally:
        unregister_program_type("tuple")


def test_cudaq_program_num_qubits():
    """Tests that the number of qubits in a CUDAQ program is correctly determined."""

    qasm = """
    OPENQASM 3;
    include "stdgates.inc";
    qubit[2] q;
    bit[2] b;
    h q[0];
    cx q[0], q[1];
    b[0] = measure q[0];
    b[1] = measure q[1];
    """

    kernel = transpile(qasm, "cudaq")

    program = load_program(kernel)

    assert isinstance(program, CudaQKernel)
    assert program.qubits == [0, 1]
    assert program.num_qubits == 2
    assert program.num_clbits == 0
