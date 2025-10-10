# Copyright 2025 qBraid
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Unit tests for qasm2 cirq_custom gates

"""

import numpy as np
from cirq import IdentityGate, TwoQubitDiagonalGate

from qbraid.transpiler.conversions.qasm2.cirq_custom import RZZGate, U2Gate, U3Gate, rzz


def test_u2_gate():
    """Test U2Gate"""
    gate = U2Gate(0, 0)
    assert str(gate) == "U2(0,0)"
    assert gate._circuit_diagram_info_(None) == "U2(0.0, 0.0)"


def test_u3_gate():
    """Test U3Gate"""
    gate = U3Gate(0, 0, 0)
    assert str(gate) == "U3(0,0,0)"
    assert gate._circuit_diagram_info_(None) == "U3(0.0, 0.0, 0.0)"


class FakeArgs:
    """Fake Args class for testing"""

    def __init__(self, precision=None):
        self.precision = precision


def test_rzz_gate():
    """Test RZZGate"""
    rads = 0.2
    gate = RZZGate(rads)

    itheta2 = 1j * rads * np.pi / 2
    expected_unitary = np.array(
        [
            [np.exp(-itheta2), 0, 0, 0],
            [0, np.exp(itheta2), 0, 0],
            [0, 0, np.exp(itheta2), 0],
            [0, 0, 0, np.exp(-itheta2)],
        ],
    )
    assert gate._num_qubits_() == 2
    assert gate._unitary_().all() == expected_unitary.all()
    assert gate._circuit_diagram_info_(args=FakeArgs(1)).wire_symbols[0] == "RZZ(0.2)"


def test_rzz_gate_method():
    """Test rzz method"""
    id_gate = rzz(0)
    assert isinstance(id_gate, IdentityGate)

    diagonal = rzz(2)
    assert isinstance(diagonal, TwoQubitDiagonalGate)

    random_rzz = rzz(0.5)
    assert isinstance(random_rzz, RZZGate)
