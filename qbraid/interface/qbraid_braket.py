import numpy as np
from braket.circuits import Circuit, Instruction
from braket.circuits.unitary_calculation import calculate_unitary


def _contiguous_expansion(circuit: Circuit) -> Circuit:
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


def _contiguous_compression(
    circuit: Circuit, rev_qubits=False
) -> Circuit:
    """Checks whether the circuit uses contiguous qubits/indices,
    and if not, reduces dimension accordingly."""
    qubit_map = {}
    circuit_qubits = list(circuit.qubits)
    circuit_qubits.sort()
    if rev_qubits:
        circuit_qubits = list(reversed(circuit_qubits))
    for index, qubit in enumerate(circuit_qubits):
        qubit_map[int(qubit)] = index
    contig_circuit = Circuit()
    for instr in circuit.instructions:
        contig_qubits = [qubit_map[int(qubit)] for qubit in list(instr.target)]
        contig_instr = Instruction(instr.operator, target=contig_qubits)
        contig_circuit.add_instruction(contig_instr)
    return contig_circuit


def _convert_to_contiguous_braket(
    circuit: Circuit, rev_qubits=False, expansion=False
) -> Circuit:
    if expansion:
        return _contiguous_expansion(circuit)
    return _contiguous_compression(circuit, rev_qubits=rev_qubits)


def unitary_from_braket(circuit: Circuit, ensure_contiguous=False) -> np.ndarray:
    """Calculate unitary of a braket circuit."""
    input_circuit = circuit if not ensure_contiguous else _convert_to_contiguous_braket(circuit)
    return calculate_unitary(input_circuit.qubit_count, input_circuit.instructions)
