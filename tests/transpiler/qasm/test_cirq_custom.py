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
Unit tests for qasm2 cirq_custom gates

"""

from qbraid.transpiler.conversions.qasm2.cirq_custom import RZZGate, U2Gate, U3Gate


def test_u2_gate():
    """Test U2Gate"""
    gate = U2Gate(0, 0)
    assert gate._circuit_diagram_info_(None) == "U2(0.0, 0.0)"


def test_u3_gate():
    """Test U3Gate"""
    gate = U3Gate(0, 0, 0)
    assert gate._circuit_diagram_info_(None) == "U3(0.0, 0.0, 0.0)"


class FakeArgs:
    """Fake Args class for testing"""
    def __init__(self, precision=None):
        self.precision = precision


def test_rzz_gate():
    """Test RZZGate"""
    gate = RZZGate(0)
    assert gate._circuit_diagram_info_(args=FakeArgs(1)).wire_symbols[0] == "RZZ(0.0)"
