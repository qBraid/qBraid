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

from qbraid.transforms.qasm3.transform import convert_to_basis_gates


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
def test_convert_to_basis_gates(original_program, expected_program):
    """Test conversion of QASM3 program to basis gates"""
    basis_gates = [
        "x",
        "y",
        "z",
        "rx",
        "ry",
        "rz",
        "h",
        "cx",
        "s",
        "sdg",
        "t",
        "tdg",
        "sx",
        "sxdg",
        "swap",
    ]

    converted_program = convert_to_basis_gates(original_program, basis_gates)

    assert converted_program == expected_program
