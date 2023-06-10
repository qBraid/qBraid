# Copyright (C) 2023 qBraid
#
# This file is part of the qBraid-SDK
#
# The qBraid-SDK is free software released under the GNU General Public License v3
# or later. You can redistribute and/or modify it under the terms of the GPL v3.
# See the LICENSE file in the project root or <https://www.gnu.org/licenses/gpl-3.0.html>.
#
# THERE IS NO WARRANTY for the qBraid-SDK, as per Section 15 of the GPL v3.

from qbraid.interface.qbraid_qasm.circuit_drawer import draw_circuit

qasm_str_1 = "\n".join(
    [
        "bit[3] b;",
        "qubit[4] q;",
        "cx q[0], q[1];",
        "cy q[1], q[3];",
        "cz q[2], q[0];",
        "b[0] = measure q[0];",
        "b[1] = measure q[1];",
        "b[2] = measure q[2];",
    ]
)

qasm_str_1_output = "\n".join(
    [
        "                   |----|  |---|",
        "q0------■----------| cz |--| m |",
        "        |          |----|  |---|",
        "     |----|           |      ║  |---|",
        "q1---| cx |-----■-----|------║--| m |",
        "     |----|     |     |      ║  |---|",
        "                |     |      ║    ║  |---|",
        "q2--------------|-----■------║----║--| m |",
        "                |            ║    ║  |---|",
        "             |----|          ║    ║    ║",
        "q3-----------| cy |----------║----║----║",
        "             |----|          ║    ║    ║",
        "                             ║    ║    ║",
        "c0=======================================",
        "                                  ║    ║",
        "                                  ║    ║",
        "c1=======================================",
        "                                       ║",
        "                                       ║",
        "c2=======================================",
    ]
)

qasm_str_2 = "\n".join(
    [
        "bit[2] b;",
        "qubit[2] q;",
        "dcx q[0], q[1];",
        "y q[1];",
        "cx q[1], q[0];",
        "b[0] = measure q[0];",
        "b[1] = measure q[1];",
    ]
)

qasm_str_2_output = "\n".join(
    [
        "     |-----|         |----|  |---|",
        "q0---|0    |---------| cx |--| m |",
        "     |     |         |----|  |---|",
        "     |  dcx|  |---|     |      ║  |---|",
        "q1---|1    |--| y |-----■------║--| m |",
        "     |-----|  |---|            ║  |---|",
        "                               ║    ║",
        "c0====================================",
        "                                    ║",
        "                                    ║",
        "c1====================================",
    ]
)


def test_circuit_drawer():
    """Tests the qasm circuit drawer"""
    assert draw_circuit(qasm_str_1) == qasm_str_1_output
    assert draw_circuit(qasm_str_2) == qasm_str_2_output
