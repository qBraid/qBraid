"""
Module containing pyQuil tools

"""
import numpy as np
from pytket.circuit import Circuit as TKCircuit, Command as TKInstruction


def _unitary_from_pytket(circuit: TKCircuit) -> np.ndarray:
    """Return the unitary of a pytket circuit."""
    return circuit.get_unitary()


def _gate_to_matrix_pytket(gate: TKInstruction) -> np.ndarray:
    """Return the unitary of the Command"""
    gate_op = gate.op
    TK_circuit = TKCircuit(gate_op.n_qubits)
    TK_circuit.add_gate(gate_op.type, gate_op.params, gate.qubits)
    return TK_circuit.get_unitary()


def _convert_to_contiguous_pytket(circuit: TKCircuit, rev_qubits=False) -> TKCircuit:
    """delete qubit with no gate and optional reverse circuit"""
    if rev_qubits:
        new_c = TKCircuit(circuit.n_qubits)
        for gate in circuit.get_commands():
            circuit_qubits = gate.qubits
            circuit_qubits = [(circuit.n_qubits - 1) - qubits.index[0] for qubits in circuit_qubits]
            gate_op = gate.op
            # devide parameter by pi, from radian to degree
            new_c.add_gate(
                gate_op.type,
                np.array(gate_op.params) / np.pi if gate_op.params else gate_op.params,
                circuit_qubits,
            )
        circuit = new_c
    circuit.remove_blank_wires()
    return circuit
