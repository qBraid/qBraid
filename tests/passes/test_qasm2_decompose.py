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
Unit tests for QASM transform to basic gates

"""

import pytest

from qbraid.passes.exceptions import QasmDecompositionError
from qbraid.passes.qasm2.decompose import decompose_qasm_qelib1


cu = """
OPENQASM 2.0;
include "qelib1.inc";
qreg q[2];
cu(0.1,0.2,0.3) q[0],q[1];
"""

rxx = """
OPENQASM 2.0;
include "qelib1.inc";
qreg q[2];"
rxx( q[0];
"""

rccx = """
OPENQASM 2.0;
include "qelib1.inc";
qreg q[3];
rccx q[0],q[1];
"""

rc3x = """
OPENQASM 2.0;
include "qelib1.inc";
qreg q[4];
rc3x q[0],q[1],q[2];
"""

@pytest.mark.parametrize("program", [cu, rxx, rccx, rc3x])
def test_fail_decompose_instr(program):
    with pytest.raises(QasmDecompositionError):
        decompose_qasm_qelib1(program)


rxx_none = """
OPENQASM 2.0;
include "qelib1.inc";
qreg q[2];"
rxx( q[0], q[1];
"""

def test_decompose_none():
    assert "rz(None)" in decompose_qasm_qelib1(rxx_none)