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
Unit tests for conversions between Cirq circuits and pytket circuits.

"""
import pytest

try:
    import numpy as np
    from cirq import Circuit, LineQubit, ops, testing
    from pytket.circuit import Circuit as TKCircuit
    from pytket.qasm import circuit_to_qasm_str

    from qbraid.interface import circuits_allclose
    from qbraid.transpiler.conversions.qasm2 import qasm2_to_cirq
    from qbraid.transpiler.converter import transpile

    from ..cirq_utils import _equal

    pytket_not_installed = False
except ImportError:
    pytket_not_installed = True

pytestmark = pytest.mark.skipif(pytket_not_installed, reason="pytket not installed")


def test_bell_state_to_from_circuits():
    """Tests cirq.Circuit --> pytket.circuit.Circuit --> cirq.Circuit
    with a Bell state circuit.
    """
    qreg = LineQubit.range(2)
    cirq_circuit = Circuit([ops.H.on(qreg[0]), ops.CNOT.on(qreg[0], qreg[1])])
    pytket_circuit = transpile(cirq_circuit, "pytket")  # pytket from Cirq
    circuit_cirq = transpile(pytket_circuit, "cirq")  # Cirq from pytket
    assert np.allclose(cirq_circuit.unitary(), circuit_cirq.unitary())


def test_random_circuit_to_from_circuits():
    """Tests cirq.Circuit --> pytket.circuit.Circuit --> cirq.Circuit
    with a random two-qubit circuit.
    """
    cirq_circuit = testing.random_circuit(qubits=2, n_moments=10, op_density=0.99, random_state=1)
    pytket_circuit = transpile(cirq_circuit, "pytket")
    circuit_cirq = transpile(pytket_circuit, "cirq")
    assert np.allclose(cirq_circuit.unitary(), circuit_cirq.unitary())


@pytest.mark.parametrize("as_qasm", (True, False))
def test_convert_with_barrier(as_qasm):
    """Tests converting a pytket circuit with a barrier to a Cirq circuit."""
    n = 5
    pytket_circuit = TKCircuit(n)
    pytket_circuit.add_barrier(list(range(n)))

    if as_qasm:
        cirq_circuit = qasm2_to_cirq(circuit_to_qasm_str(pytket_circuit))
    else:
        cirq_circuit = transpile(pytket_circuit, "cirq")

    assert _equal(cirq_circuit, Circuit())


@pytest.mark.parametrize("as_qasm", (True, False))
def test_convert_with_multiple_barriers(as_qasm):
    """Tests converting a pytket circuit with barriers to a Cirq circuit."""
    n = 1
    num_ops = 10

    pytket_circuit = TKCircuit(n)
    for _ in range(num_ops):
        for i in range(n):
            pytket_circuit.H(i)
        pytket_circuit.add_barrier(list(range(n)))

    if as_qasm:
        cirq_circuit = qasm2_to_cirq(circuit_to_qasm_str(pytket_circuit))
    else:
        cirq_circuit = transpile(pytket_circuit, "cirq")

    qbit = LineQubit(0)
    correct = Circuit(ops.H.on(qbit) for _ in range(num_ops))
    assert _equal(cirq_circuit, correct)
    assert circuits_allclose(pytket_circuit, cirq_circuit, strict_gphase=True)
