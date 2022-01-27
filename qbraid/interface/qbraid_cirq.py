from typing import List, Sequence

import numpy as np

from cirq import (
    LineQubit,
    GridQubit,
    NamedQubit,
    Circuit,
    I,

)
from cirq.ops import Qid

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
    for op in circuit.all_operations():
        qubit_indicies = [qubit_map[_key_from_qubit(q)] for q in op.qubits]
        line_qubits = [LineQubit(i) for i in qubit_indicies]
        line_qubit_circuit.append(op.gate.on(*line_qubits))
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
            "Expected qubit of type 'GridQubit' or 'LineQubit'"
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
            "Expected qubit of type 'GridQubit' or 'LineQubit'"
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

def _convert_to_contiguous_cirq(circuit: Circuit) -> Circuit:
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
        for q in cirq_qubits:
            circuit.append(I(q))
    return circuit

def unitary_from_cirq(circuit: Circuit, ensure_contiguous=False) -> np.ndarray:
    """Calculate unitary of a cirq circuit."""
    input_circuit = circuit if not ensure_contiguous else _convert_to_contiguous_cirq(circuit)
    return input_circuit.unitary()

