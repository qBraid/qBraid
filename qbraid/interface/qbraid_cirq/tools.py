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
Module containing Cirq tools

"""
from copy import deepcopy
from typing import List, Sequence, Union

import numpy as np
from cirq import Circuit, GridQubit, I, LineQubit, MeasurementGate, NamedQubit, Qid, ops

QUBIT = Union[LineQubit, GridQubit, NamedQubit, Qid]


def _unitary_from_cirq(circuit: Circuit) -> np.ndarray:
    """Return the unitary of a Cirq circuit."""
    return circuit.unitary()


def _convert_to_line_qubits(
    circuit: Circuit,
    rev_qubits=False,
) -> Circuit:
    """Converts a Cirq circuit constructed using NamedQubits to
    a Cirq circuit constructed using LineQubits."""
    qubits = list(circuit.all_qubits())
    qubits.sort()
    if rev_qubits:
        qubits = list(reversed(qubits))
    qubit_map = {_key_from_qubit(q): i for i, q in enumerate(qubits)}
    line_qubit_circuit = Circuit()
    for opr in circuit.all_operations():
        qubit_indicies = [qubit_map[_key_from_qubit(q)] for q in opr.qubits]
        line_qubits = [LineQubit(i) for i in qubit_indicies]
        line_qubit_circuit.append(opr.gate.on(*line_qubits))
    return line_qubit_circuit


def _key_from_qubit(qubit: Qid) -> str:
    if isinstance(qubit, LineQubit):
        key = str(qubit)
    elif isinstance(qubit, GridQubit):
        key = str(qubit.row)
    elif isinstance(qubit, NamedQubit):
        # Only correct if numbered sequentially
        key = str(qubit.name)
    else:
        raise ValueError(
            "Expected qubit of type 'GridQubit' 'LineQubit' or 'NamedQubit'"
            f"but instead got {type(qubit)}"
        )
    return key


def _int_from_qubit(qubit: Qid) -> int:
    if isinstance(qubit, LineQubit):
        index = int(qubit)
    elif isinstance(qubit, GridQubit):
        index = qubit.row
    elif isinstance(qubit, NamedQubit):
        # Only correct if numbered sequentially
        index = int(qubit._comparison_key().split(":")[0][7:])
    else:
        raise ValueError(
            "Expected qubit of type 'GridQubit' 'LineQubit' or 'NamedQubit'"
            f"but instead got {type(qubit)}"
        )
    return index


def _make_qubits(circuit: Circuit, qubits: List[int]) -> Sequence[Qid]:
    qubit_obj = list(circuit.all_qubits())[0]
    if isinstance(qubit_obj, LineQubit):
        qids = [LineQubit(i) for i in qubits]
    elif isinstance(qubit_obj, GridQubit):
        qids = [GridQubit(i, qubit_obj.col) for i in qubits]
    elif isinstance(qubit_obj, NamedQubit):
        qids = [NamedQubit(str(i)) for i in qubits]
    else:
        raise ValueError(
            "Expected qubits of type 'GridQubit', 'LineQubit', or "
            f"'NamedQubit' but instead got {type(qubit_obj)}"
        )
    return qids


def _contiguous_expansion(circuit: Circuit) -> Circuit:
    """Checks whether the circuit uses contiguous qubits/indices,
    and if not, adds identity gates to vacant registers as needed."""
    nqubits = 0
    max_qubit = 0
    occupied_qubits = []
    cirq_qubits = list(circuit.all_qubits())
    if isinstance(cirq_qubits[0], NamedQubit):
        return _convert_to_line_qubits(circuit)
    for qubit in circuit.all_qubits():
        index = _int_from_qubit(qubit)
        occupied_qubits.append(index)
        if index > max_qubit:
            max_qubit = index
        nqubits += 1
    qubit_count = max_qubit + 1
    if qubit_count > nqubits:
        all_qubits = list(range(0, qubit_count))
        vacant_qubits = list(set(all_qubits) - set(occupied_qubits))
        cirq_qubits = _make_qubits(circuit, vacant_qubits)
        for qubit in cirq_qubits:
            circuit.append(I(qubit))
    return circuit


def _contiguous_compression(circuit: Circuit, rev_qubits=False) -> Circuit:
    """Checks whether the circuit uses contiguous qubits/indices,
    and if not, reduces dimension accordingly."""
    qubit_map = {}
    circuit_qubits = list(circuit.all_qubits())
    circuit_qubits.sort()
    if rev_qubits:
        circuit_qubits = list(reversed(circuit_qubits))
    for index, qubit in enumerate(circuit_qubits):
        qubit_map[_int_from_qubit(qubit)] = index
    contig_circuit = Circuit()
    for opr in circuit.all_operations():
        contig_indicies = [qubit_map[_int_from_qubit(qubit)] for qubit in opr.qubits]
        contig_qubits = _make_qubits(circuit, contig_indicies)
        contig_circuit.append(opr.gate.on(*contig_qubits))
    return contig_circuit


def _convert_to_contiguous_cirq(circuit: Circuit, rev_qubits=False, expansion=False) -> Circuit:
    if expansion:
        return _contiguous_expansion(circuit)
    return _contiguous_compression(circuit, rev_qubits=rev_qubits)


def is_measurement_gate(op):
    """Returns whether Cirq gate/operation is MeasurementGate."""
    return isinstance(op, ops.MeasurementGate) or isinstance(
        getattr(op, "gate", None), ops.MeasurementGate
    )


def _equal(
    circuit_one: Circuit,
    circuit_two: Circuit,
    require_qubit_equality: bool = False,
    require_measurement_equality: bool = False,
) -> bool:
    """Returns True if the circuits are equal, else False.

    Args:
        circuit_one: Input circuit to compare to circuit_two.
        circuit_two: Input circuit to compare to circuit_one.
        require_qubit_equality: Requires that the qubits be equal
            in the two circuits.
        require_measurement_equality: Requires that measurements are equal on
            the two circuits, meaning that measurement keys are equal.

    Note:
        If set(circuit_one.all_qubits()) = {LineQubit(0)},
        then set(circuit_two_all_qubits()) must be {LineQubit(0)},
        else the two are not equal.
        If True, the qubits of both circuits must have a well-defined ordering.
    """
    # Make a deepcopy only if it's necessary
    if not (require_qubit_equality and require_measurement_equality):
        circuit_one = deepcopy(circuit_one)
        circuit_two = deepcopy(circuit_two)

    if not require_qubit_equality:
        # Transform the qubits of circuit one to those of circuit two
        qubit_map = dict(
            zip(
                sorted(circuit_one.all_qubits()),
                sorted(circuit_two.all_qubits()),
            )
        )
        circuit_one = circuit_one.transform_qubits(lambda q: qubit_map[q])

    if not require_measurement_equality:
        for circ in (circuit_one, circuit_two):
            measurements = [
                (moment, op)
                for moment, op, _ in circ.findall_operations_with_gate_type(MeasurementGate)
            ]
            circ.batch_remove(measurements)
    return circuit_one == circuit_two
