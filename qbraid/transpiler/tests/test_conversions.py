# Copyright 2023 qBraid
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
Unit tests for the qbraid transpiler conversions module.

"""
import cirq
import numpy as np
import pytest

from qbraid._qprogram import QPROGRAM_LIBS
from qbraid.interface import to_unitary
from qbraid.transpiler.conversions import convert_from_cirq


@pytest.mark.parametrize("frontend", QPROGRAM_LIBS)
def test_convert_circuit_operation_from_cirq(frontend):
    q = cirq.NamedQubit("q")
    cirq_circuit = cirq.Circuit(
        cirq.Y(q), cirq.CircuitOperation(cirq.FrozenCircuit(cirq.X(q)), repetitions=5), cirq.Z(q)
    )

    test_circuit = convert_from_cirq(cirq_circuit, frontend)

    cirq_unitary = to_unitary(cirq_circuit)
    test_unitary = to_unitary(test_circuit)

    assert np.allclose(cirq_unitary, test_unitary)
