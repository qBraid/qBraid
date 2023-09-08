# Copyright (C) 2023 qBraid
#
# This file is part of the qBraid-SDK
#
# The qBraid-SDK is free software released under the GNU General Public License v3
# or later. You can redistribute and/or modify it under the terms of the GPL v3.
# See the LICENSE file in the project root or <https://www.gnu.org/licenses/gpl-3.0.html>.
#
# THERE IS NO WARRANTY for the qBraid-SDK, as per Section 15 of the GPL v3.

"""
Unit tests for OpenQASM 3 circuit drawer

"""

import pytest

from qbraid.interface.qbraid_qasm3.circuit_drawer import draw_circuit

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
        "q0------■----------| cz |--| m |-----------",
        "        |          |----|  |---|",
        "     |----|           |      ║  |---|",
        "q1---| cx |-----■-----|------║--| m |------",
        "     |----|     |     |      ║  |---|",
        "                |     |      ║    ║  |---|",
        "q2--------------|-----■------║----║--| m |-",
        "                |            ║    ║  |---|",
        "             |----|          ║    ║    ║",
        "q3-----------| cy |----------║----║----║---",
        "             |----|          ║    ║    ║",
        "                             ║    ║    ║",
        "c0=========================================",
        "                                  ║    ║",
        "                                  ║    ║",
        "c1=========================================",
        "                                       ║",
        "                                       ║",
        "c2=========================================",
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
        "q0---|0    |---------| cx |--| m |------",
        "     |     |         |----|  |---|",
        "     |  dcx|  |---|     |      ║  |---|",
        "q1---|1    |--| y |-----■------║--| m |-",
        "     |-----|  |---|            ║  |---|",
        "                               ║    ║",
        "c0======================================",
        "                                    ║",
        "                                    ║",
        "c1======================================",
    ]
)

qasm_str_3 = "\n".join(
    [
        "OPENQASM 3;",
        'include "stdgates.inc";',
        "qubit[3] _all_qubits;",
        "let q = _all_qubits[0:2];",
        "swap q[0], q[2];",
        "swap q[1], q[2];",
        "swap q[2], q[0];",
        "swap q[2], q[1];",
    ]
)

qasm_str_3_output = "\n".join(
    [
        "q0----X-------X-----",
        "      |       |",
        "      |       |",
        "q1----|---X---|---X-",
        "      |   |   |   |",
        "      |   |   |   |",
        "q2----X---X---X---X-",
    ]
)

qasm_str_4 = "\n".join(
    [
        "OPENQASM 3;",
        'include "stdgates.inc";',
        "qubit[4] _all_qubits;",
        "bit[3] b;",
        "let q = _all_qubits[0:3];",
        "ccz q[3], q[1], q[2];",
        "rx(3.247480918297134) q[0];",
        "swap q[2], q[3];",
        "iswap q[1], q[0];",
        "y q[3];",
        "cy q[1], q[3];",
        "swap q[1], q[2];",
        "b[0] = measure q[2];",
        "b[1] = measure q[1];",
    ]
)

qasm_str_4_output = "\n".join(
    [
        "     |-----------------------|  |-------|",
        "q0---| rx(3.247480918297134) |--|1      |----------------------------",
        "     |-----------------------|  |       |",
        "                                |  iswap|                      |---|",
        "q1---------------■--------------|0      |--------■---X---------| m |-",
        "                 |              |-------|        |   |         |---|",
        "              |-----|                            |   |  |---|    ║",
        "q2------------| ccz |---------------X------------|---X--| m |----║---",
        "              |-----|               |            |      |---|    ║",
        "                 |                  |  |---|  |----|      ║      ║",
        "q3---------------■------------------X--| y |--| cy |------║------║---",
        "                                       |---|  |----|      ║      ║",
        "                                                          ║      ║",
        "c0===================================================================",
        "                                                                 ║",
        "                                                                 ║",
        "c1===================================================================",
        "c2===================================================================",
    ]
)


@pytest.mark.parametrize(
    ("qasm_str", "expected_output"),
    [
        (qasm_str_1, qasm_str_1_output),
        (qasm_str_2, qasm_str_2_output),
        (qasm_str_3, qasm_str_3_output),
        (qasm_str_4, qasm_str_4_output),
    ],
)
def test_circuit_drawer(qasm_str, expected_output):
    """Tests the qasm circuit drawer"""
    assert draw_circuit(qasm_str) == expected_output
