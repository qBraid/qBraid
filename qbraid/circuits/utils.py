from typing import Union

import numpy as np

from braket.circuits import Circuit as BraketCircuit
from braket.circuits.unitary_calculation import calculate_unitary
from cirq import Circuit as CirqCircuit
from qiskit import QuantumCircuit as QiskitCircuit
from qiskit.quantum_info import Operator as QiskitOperator

from .exceptions import CircuitError
from .instruction import Instruction
from .moment import Moment


def validate_qubit(op: Union[Instruction, Moment], num_qubits: int) -> bool:
    """Checks that the target qubits used in instructionsa are availbale on the circuit.

    Args:
        op (Union[Instruction,Moment]): The instruction or moment to validate.
        num_qubits (int): The number of qubits in the circuit.

    """
    if not op.qubits:
        return True
    if isinstance(op, Instruction):
        if max(op.qubits) < num_qubits and np.all(np.array(op.qubits) >= 0):
            return True
        else:
            return False
    elif isinstance(op, Moment):
        # validate moment
        if max(op.qubits) > num_qubits - 1:
            raise CircuitError(
                "Index {} exceeds number of qubits {} in circuit".format(op.qubits, num_qubits)
            )
        return True
    else:
        return True


def validate_operation(
    op: Union[
        Instruction,
        Moment,
    ],
    num_qubits: int,
) -> bool:
    """Validates that the operation is an instance of an Instruction, Moment, or Circuit.

    Args:
        op (Union[ Instruction, Moment, ]): The operation that is to be validated.
        num_qubits (int): Number of circuits in the circuit

    """
    from .circuit import Circuit

    if validate_qubit(op, num_qubits) and (isinstance(op, (Instruction, Moment, Circuit))):
        return True
    else:
        raise CircuitError(
            "Operation of type {} not appendable in circuit of {} qubits".format(
                type(op), num_qubits
            )
        )


def to_unitary(circuit):
    """Calculate unitary of a braket, cirq, or qiskit circuit.
    Args:
        circuit (braket, cirq, or qiskit Circuit): The circuit object for which
            the unitary matrix will be calculated.
    Returns:
        numpy.ndarray: A numpy array representing the `circuit` as a unitary
    """
    if isinstance(circuit, BraketCircuit):
        return calculate_unitary(circuit.qubit_count, circuit.instructions)
    elif isinstance(circuit, CirqCircuit):
        return circuit.unitary()
    elif isinstance(circuit, QiskitCircuit):
        return QiskitOperator(circuit).data
    else:
        raise TypeError(f"to_unitary calculation not supported for type {type(circuit)}")
