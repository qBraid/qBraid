# Copyright (C) 2024 qBraid
#
# This file is part of the qBraid-SDK
#
# The qBraid-SDK is free software released under the GNU General Public License v3
# or later. You can redistribute and/or modify it under the terms of the GPL v3.
# See the LICENSE file in the project root or <https://www.gnu.org/licenses/gpl-3.0.html>.
#
# THERE IS NO WARRANTY for the qBraid-SDK, as per Section 15 of the GPL v3.

from __future__ import annotations

import textwrap
from typing import TYPE_CHECKING

import cudaq
import pytest
from openqasm3.parser import parse

from qbraid.transpiler.conversions.openqasm3 import openqasm3_to_cudaq

if TYPE_CHECKING:
    from cudaq.kernel.kernel_builder import PyKernel
    from openqasm3.ast import Program


@pytest.fixture
def cudaq_kernel() -> PyKernel:
    kernel = cudaq.make_kernel()

    qubit = kernel.qalloc()

    kernel.h(qubit)
    kernel.x(qubit)
    kernel.y(qubit)
    kernel.z(qubit)
    kernel.t(qubit)
    kernel.s(qubit)

    kernel.mz(qubit)

    return kernel


@pytest.fixture
def qasm_program() -> Program:
    qasm_str = """
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
    qasm_str = textwrap.dedent(qasm_str).strip()

    return parse(qasm_str)


def test_openqasm3_to_cudaq(cudaq_kernel, qasm_program):
    """Test converting an OpenQASM3 program to a CUDA-Q kernel."""
    cudaq_out = openqasm3_to_cudaq(qasm_program)
    print(str(cudaq_out), "OUT")
    print(str(cudaq_kernel), "KERNEL")
    assert str(cudaq_out) == str(cudaq_kernel)
