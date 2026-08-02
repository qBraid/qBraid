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
Module containing function to convert from Cirq's circuit
representation to pyQuil's circuit representation (Quil programs).

"""
from __future__ import annotations

from typing import TYPE_CHECKING

from cirq import Circuit, LineQubit, Moment, QubitOrder
from cirq import ops as cirq_ops
from qbraid_core._import import LazyLoader

from qbraid.transpiler.annotations import weight
from qbraid.transpiler.exceptions import ProgramConversionError

try:
    from .cirq_quil_output import QuilOutput
except ImportError:  # pragma: no cover
    QuilOutput = None

pyquil = LazyLoader("pyquil", globals(), "pyquil")

if TYPE_CHECKING:
    import cirq.circuits
    from pyquil import Program


def _merge_terminal_measurements(circuit: cirq.circuits.Circuit) -> cirq.circuits.Circuit:
    """Merge terminal measurements into one keyed measurement operation.

    QASM-derived circuits measure into per-bit keys (``c_0``, ``c_1``, ...), which the
    Quil output would otherwise declare as one ``BIT[1]`` register each -- a fragmented
    form QCS rejects for hardware execution. Mid-circuit measurements are left untouched.

    Moving a terminal measurement past later operations on other qubits is safe: disjoint
    operations commute, and classically controlled operations (the only construct that
    could observe the order) are rejected by ``QuilOutput``.
    """
    operations = list(circuit.all_operations())
    last_op_on_qubit = {}
    for op in operations:
        for qubit in op.qubits:
            last_op_on_qubit[qubit] = op
    terminal = [
        op
        for op in operations
        if isinstance(op.gate, cirq_ops.MeasurementGate)
        and all(last_op_on_qubit[q] is op for q in op.qubits)
    ]
    if len(terminal) <= 1:
        return circuit
    qubits, invert_mask = [], []
    for op in terminal:
        mask = op.gate.invert_mask + (False,) * (len(op.qubits) - len(op.gate.invert_mask))
        qubits.extend(op.qubits)
        invert_mask.extend(mask)
    merged = cirq_ops.MeasurementGate(
        num_qubits=len(qubits), key="m", invert_mask=tuple(invert_mask)
    ).on(*qubits)
    remaining = [op for op in operations if not any(op is t for t in terminal)]
    return Circuit([*remaining, Moment(merged)])


# Deliberately below e**-0.25 ~= 0.7788, the break-even at which a single conversion loses
# to two weight-1.0 hops: gate-only fidelity of this edge measures ~0.88, while routing
# through qasm2 measures ~0.95, so multi-hop routes should keep avoiding it. (Its readout
# fragmentation -- the original reason for the down-weight -- is fixed by
# ``_merge_terminal_measurements``.) See tests/transpiler/test_measurement_coverage.py.
@weight(0.74)
def cirq_to_pyquil(circuit: cirq.circuits.Circuit) -> Program:
    """Returns a pyQuil Program equivalent to the input Cirq circuit.

    Args:
        circuit: Cirq circuit to convert to a pyQuil Program.

    Returns:
        pyquil.Program object equivalent to the input Cirq circuit.
    """
    circuit = _merge_terminal_measurements(circuit)
    input_qubits = circuit.all_qubits()
    max_qubit = max(input_qubits)
    # if we are using LineQubits, keep the qubit labeling the same
    if isinstance(max_qubit, LineQubit):
        qubit_range = max_qubit.x + 1
        qubit_order = LineQubit.range(qubit_range)
    # otherwise, use the default ordering (starting from zero)
    else:
        qubit_order = QubitOrder.DEFAULT
    qubits = QubitOrder.as_qubit_order(qubit_order).order_for(input_qubits)
    operations = circuit.all_operations()
    try:
        quil_str = str(QuilOutput(operations, qubits))
        return pyquil.Program(quil_str)
    except ValueError as err:
        raise ProgramConversionError(
            f"Cirq qasm converter doesn't yet support {err.args[0][32:]}."
        ) from err
