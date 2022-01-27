import numpy as np
from braket.circuits import Circuit
from braket.circuits.unitary_calculation import calculate_unitary

def _convert_to_contiguous_braket(circuit: Circuit) -> Circuit:
    """Checks whether the circuit uses contiguous qubits/indices,
    and if not, adds identity gates to vacant registers as needed."""
    max_qubit = 0
    occupied_qubits = []
    for qubit in circuit.qubits:
        index = int(qubit)
        occupied_qubits.append(index)
        if index > max_qubit:
            max_qubit = index
    qubit_count = max_qubit + 1
    if qubit_count > circuit.qubit_count:
        all_qubits = list(range(0, qubit_count))
        vacant_qubits = list(set(all_qubits) - set(occupied_qubits))
        for index in vacant_qubits:
            circuit.i(index)
    return circuit


def unitary_from_braket(circuit: Circuit, ensure_contiguous=False) -> np.ndarray:
    """Calculate unitary of a braket circuit."""
    input_circuit = circuit if not ensure_contiguous else _convert_to_contiguous_braket(circuit)
    return calculate_unitary(input_circuit.qubit_count, input_circuit.instructions)