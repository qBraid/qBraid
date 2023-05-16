# Copyright (C) 2023 qBraid
#
# This file is part of the qBraid-SDK
#
# The qBraid-SDK is free software released under the GNU General Public License v3
# or later. You can redistribute and/or modify it under the terms of the GPL v3.
# See the LICENSE file in the project root or <https://www.gnu.org/licenses/gpl-3.0.html>.
#
# THERE IS NO WARRANTY for the qBraid-SDK, as per Section 15 of the GPL v3.

from qbraid.interface.qbraid_qasm.tools import qasm_qubits, qasm_num_qubits, qasm_depth
from qbraid.interface.qbraid_qasm.circuits import qasm_bell, qasm_shared15


def test_qasm_qubits():
    """test calculate qasm qubit"""

    assert qasm_qubits(qasm_bell()) == ["qreg q[2];"]
    assert qasm_qubits(qasm_shared15()) == ["qreg q[4];"]


def test_qasm_num_qubits():
    assert qasm_num_qubits(qasm_bell()) == 2
    assert qasm_num_qubits(qasm_shared15()) == 4


def test_qasm_depth():
    """test calcualte qasm depth"""
    assert qasm_depth(qasm_bell()) == 2
    assert qasm_depth(qasm_shared15()) == 22
