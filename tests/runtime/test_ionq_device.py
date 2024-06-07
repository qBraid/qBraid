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
Unit tests for IonQDevice

"""
import openqasm3

from qbraid.runtime.ionq import IonQDevice


def test_extract_gate_data():
    """Test extracting gate data from a OpenQASM 3 program."""
    qasm3_str = """
OPENQASM 3.0;
include "stdgates.inc";
qubit[3] q;
x q[0];
not q[1];
y q[0];
z q[0];
rx(pi / 4) q[0];
ry(pi / 2) q[0];
rz(3 * pi / 4) q[0];
h q[0];
cx q[0], q[1];
CX q[1], q[2];
cnot q[2], q[0];
ccx q[0], q[1], q[2];
toffoli q[2], q[1], q[0];
s q[0];
sdg q[0];
si q[0];
t q[0];
tdg q[0];
ti q[1];
sx q[0];
v q[1];
sxdg q[0];
vi q[1];
swap q[0], q[1];
"""
    expected = [
        {"gate": "x", "target": 0},
        {"gate": "not", "target": 1},
        {"gate": "y", "target": 0},
        {"gate": "z", "target": 0},
        {"gate": "rx", "target": 0, "rotation": 0.7853981633974483},
        {"gate": "ry", "target": 0, "rotation": 1.5707963267948966},
        {"gate": "rz", "target": 0, "rotation": 2.356194490192345},
        {"gate": "h", "target": 0},
        {"gate": "cnot", "control": 0, "target": 1},
        {"gate": "cnot", "control": 1, "target": 2},
        {"gate": "cnot", "control": 2, "target": 0},
        {"gate": "cnot", "controls": [0, 1], "target": 2},
        {"gate": "cnot", "controls": [2, 1], "target": 0},
        {"gate": "s", "target": 0},
        {"gate": "si", "target": 0},
        {"gate": "si", "target": 0},
        {"gate": "t", "target": 0},
        {"gate": "ti", "target": 0},
        {"gate": "ti", "target": 1},
        {"gate": "v", "target": 0},
        {"gate": "v", "target": 1},
        {"gate": "vi", "target": 0},
        {"gate": "vi", "target": 1},
        {"gate": "swap", "targets": [0, 1]},
    ]
    qasm3_program = openqasm3.parser.parse(qasm3_str)
    actual = IonQDevice.extract_gate_data(qasm3_program)

    assert actual == expected
