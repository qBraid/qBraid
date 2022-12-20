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
Module containing Cirq tools

"""
from typing import List, Sequence, Union

import numpy as np
from cirq import Circuit, GridQubit, I, LineQubit, NamedQubit, Qid

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
