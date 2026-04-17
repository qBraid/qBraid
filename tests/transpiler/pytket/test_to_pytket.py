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
Unit tests for conversions between Cirq circuits and pytket circuits.

"""
import importlib.util

import numpy as np
import pytest
from cirq import Circuit, LineQubit, ops, testing

from qbraid.interface import circuits_allclose
from qbraid.transpiler import ProgramConversionError, transpile

pytket_not_installed = importlib.util.find_spec("pytket") is None
pytestmark = pytest.mark.skipif(pytket_not_installed, reason="pytket not installed")


def test_bell_state_to_pytket():
    """Tests Circuit --> pytket.circuit.Circuit --> Circuit
    with a Bell state circuit.
    """
    qreg = LineQubit.range(2)
    cirq_circuit = Circuit([ops.H.on(qreg[0]), ops.CNOT.on(qreg[0], qreg[1])])
    pytket_circuit = transpile(cirq_circuit, "pytket")
    assert circuits_allclose(pytket_circuit, cirq_circuit, strict_gphase=True)


@pytest.mark.parametrize("num_qubits", [1, 2, 3, 4, 5])
def test_random_circuit_to_pytket(num_qubits):
    """Test converting random Cirq circuits to pytket."""
    for _ in range(10):
        cirq_circuit = testing.random_circuit(
            qubits=num_qubits,
            n_moments=np.random.randint(1, 6),
            op_density=1,
            random_state=np.random.randint(1, 10),
        )
        pytket_circuit = transpile(cirq_circuit, "pytket")
        assert circuits_allclose(pytket_circuit, cirq_circuit, strict_gphase=True)


def test_raise_error():
    """Test raising error for unsupported gates."""
    with pytest.raises(ProgramConversionError):
        probs = np.random.uniform(low=0, high=0.5)
        cirq_circuit = Circuit(ops.PhaseDampingChannel(probs).on(*LineQubit.range(1)))
        transpile(cirq_circuit, "pytket", require_native=True)
