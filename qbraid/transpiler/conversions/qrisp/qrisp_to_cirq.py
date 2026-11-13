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
Module defining Qrisp conversions

"""

from __future__ import annotations

from typing import TYPE_CHECKING

from qbraid_core._import import LazyLoader

from qbraid.transpiler.annotations import weight

cirq = LazyLoader("cirq", globals(), "cirq")
qrisp = LazyLoader("qrisp", globals(), "qrisp")

if TYPE_CHECKING:
    import qrisp as qrisp_
    from cirq import Circuit


# U3Gate names that qrisp's Cirq converter maps itself.
_MAPPED_U3_NAMES = frozenset(
    ("h", "rx", "ry", "rz", "p", "s", "s_dg", "t", "t_dg", "id", "sx", "sx_dg", "gphase")
)


def _is_unmapped(op: qrisp_.Operation) -> bool:
    """True for gates qrisp's Cirq converter can't convert correctly.

    That is a U3Gate it has no name for (u3, r, r_dg, id_dg, ...), which it fails on, and a
    controlled Y, which it either fails on (cy) or decomposes to a controlled -Y (2cy, ...).
    """
    if isinstance(op, qrisp.U3Gate):
        return op.name not in _MAPPED_U3_NAMES
    return isinstance(op, qrisp.circuit.ControlledOperation) and op.base_operation.name == "y"


def _contains_unmapped(op: qrisp_.Operation) -> bool:
    if _is_unmapped(op):
        return True
    return op.definition is not None and any(_contains_unmapped(i.op) for i in op.definition.data)


def _rewrite_unmapped(qrisp_qc: qrisp_.QuantumCircuit) -> qrisp_.QuantumCircuit:
    """Return a copy of the circuit with every unmapped gate rewritten exactly, phase included.

    Composites containing one are inlined first, at any depth: qrisp's converter inlines
    composites itself only after this runs, so a nested gate would otherwise reach it.
    """
    if not any(_contains_unmapped(instr.op) for instr in qrisp_qc.data):
        return qrisp_qc
    # pylint: disable-next=import-outside-toplevel
    from qrisp.circuit.transpiler import transpile

    flat = transpile(
        qrisp_qc,
        transpile_predicate=lambda op: not _is_unmapped(op) and _contains_unmapped(op),
    )
    rewritten = flat.clearcopy()
    for instr in flat.data:
        op = instr.op
        if not _is_unmapped(op):
            rewritten.append(op, instr.qubits, instr.clbits)
        elif isinstance(op, qrisp.U3Gate):
            qubit = instr.qubits[0]
            rewritten.rz(op.lam, qubit)
            rewritten.ry(op.theta, qubit)
            rewritten.rz(op.phi, qubit)
            rewritten.gphase((op.phi + op.lam) / 2 + op.global_phase, qubit)
        else:
            # Y = S X S^dagger, so conjugating the controlled X by S keeps controls and ctrl_state.
            target = instr.qubits[-1]
            rewritten.s_dg(target)
            rewritten.append(
                qrisp.XGate().control(len(op.controls), ctrl_state=op.ctrl_state), instr.qubits
            )
            rewritten.s(target)
    return rewritten


@weight(1)
def qrisp_to_cirq(qrisp_qc: qrisp_.QuantumCircuit) -> Circuit:
    """Returns a Cirq circuit equivalent to the input Qrisp circuit.

    Args:
        qrisp_qc: Qrisp circuit to convert to a Cirq circuit.

    Returns:
        Cirq Circuit object equivalent to the input Qrisp circuit.
    """
    circuit = _rewrite_unmapped(qrisp_qc).to_cirq()
    # qrisp emits extended-precision (numpy.longdouble) gate exponents, which cirq's QASM
    # exporter cannot format ("Invalid format specifier 'half_turns'"). Recast them to
    # plain Python float so downstream to_qasm() works.
    normalized = cirq.Circuit()
    for op in circuit.all_operations():
        gate = op.gate
        exponent = getattr(gate, "_exponent", None)
        if exponent is None or isinstance(exponent, (int, float)):
            pass
        elif isinstance(gate, (cirq.Rx, cirq.Ry, cirq.Rz)):
            # These take rads, not exponent and global_shift.
            gate = type(gate)(rads=float(gate._rads))  # pylint: disable=protected-access
        else:
            global_shift = float(getattr(gate, "_global_shift", 0.0))
            try:
                gate = type(gate)(exponent=float(exponent), global_shift=global_shift)
            except TypeError:
                gate = type(gate)(exponent=float(exponent))
        normalized.append(gate.on(*op.qubits))
    return normalized
