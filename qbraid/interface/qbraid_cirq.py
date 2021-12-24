import cirq
import numpy as np

def int_from_qubit(qubit):
    if isinstance(qubit, cirq.LineQubit):
        return int(qubit)
    if isinstance(qubit, cirq.GridQubit):
        return qubit.row
    raise ValueError(
        f"Expected qubit of type 'GridQubit' or 'LineQubit' but instead got {type(qubit)}"
    )

def make_qubits(circuit, qubit_index_lst):
    qubit = list(circuit.all_qubits())[0]
    if isinstance(qubit, cirq.LineQubit):
        return [cirq.LineQubit(i) for i in qubit_index_lst]
    if isinstance(qubit, cirq.GridQubit):
        return [cirq.GridQubit(i, qubit.col) for i in qubit_index_lst]

def make_contiguous(circuit):
    nqubits = 0
    max_qubit = 0
    occupied_qubits = []
    for qubit in circuit.all_qubits():
        index = int_from_qubit(qubit)
        occupied_qubits.append(index)
        if index > max_qubit:
            max_qubit = index
        nqubits += 1
    qubit_count = max_qubit + 1
    if qubit_count > nqubits:
        all_qubits = list(range(0,qubit_count))
        vacant_qubits = list(set(all_qubits) - set(occupied_qubits))
        cirq_qubits = make_qubits(circuit, vacant_qubits)
        for cirq_qubit in cirq_qubits:
            circuit.append(cirq.I(cirq_qubit))
    return circuit

def unitary_from_cirq(circuit: cirq.Circuit) -> np.ndarray:
    """Calculate unitary of a cirq circuit."""
    contiguous_circuit = make_contiguous(circuit)
    return contiguous_circuit.unitary()

