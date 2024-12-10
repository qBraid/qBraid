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
Unit tests for OpenQASM 3.0 to CUDA-Q kernel transpilation.

"""
from __future__ import annotations

from typing import TYPE_CHECKING

import cudaq
import pytest
from openqasm3.parser import parse
from qiskit.qasm3 import loads as qasm3_loads

from qbraid.interface import circuits_allclose
from qbraid.transpiler.conversions.openqasm3 import openqasm3_to_cudaq, openqasm3_to_qasm3
from qbraid.transpiler.conversions.qasm2.qasm2_to_qasm3 import qasm2_to_qasm3

if TYPE_CHECKING:
    from cudaq.kernel.kernel_builder import PyKernel
    from openqasm3.ast import Program


@pytest.fixture
def qasm_program() -> Program:
    """An example OpenQASM 3.0 program on a single qubit."""
    q_str = """
    OPENQASM 3.0;
    include "stdgates.inc";

    qubit[1] q;
    bit[1] b;

    h q[0];
    x q[0];
    y q[0];
    z q[0];
    t q[0];
    s q[0];

    b[0] = measure q[0];
    """
    return parse(q_str)


def test_openqasm3_to_cudaq(qasm_program):
    """Test converting an OpenQASM3 program to a CUDA-Q kernel."""
    cudaq_out = openqasm3_to_cudaq(qasm_program)
    qasm2_str_out = cudaq.translate(cudaq_out, format="openqasm2")
    qasm3_str_out = qasm2_to_qasm3(qasm2_str_out)
    qasm3_str_in = openqasm3_to_qasm3(qasm_program)

    assert circuits_allclose(qasm3_loads(qasm3_str_out), qasm3_loads(qasm3_str_in))
