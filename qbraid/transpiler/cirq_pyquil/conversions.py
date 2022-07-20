"""
Module containing functions to convert between Cirq's circuit
representation and pyQuil's circuit representation (Quil programs).

"""
from cirq import Circuit, LineQubit
from cirq_rigetti.quil_input import circuit_from_quil
from cirq_rigetti.quil_output import QuilOutput
from pyquil import Program

from qbraid.interface.convert_to_contiguous import convert_to_contiguous
from qbraid.interface.qbraid_cirq.tools import _convert_to_line_qubits

QuilType = str


def to_quil(circuit: Circuit) -> QuilType:
    """Returns a Quil string representing the input Cirq circuit.

    Args:
        circuit: Cirq circuit to convert to a Quil string.

    Returns:
        QuilType: Quil string equivalent to the input Cirq circuit.
    """
    circuit = _convert_to_line_qubits(circuit)
    operations = circuit.all_operations()
    qubits = circuit.all_qubits()
    max_qubit = max(qubits)
    qubit_range = max_qubit.x + 1
    qubits = LineQubit.range(qubit_range)
    output = QuilOutput(operations, qubits)
    return str(output)


def to_pyquil(circuit: Circuit, compat=True) -> Program:
    """Returns a pyQuil Program equivalent to the input Cirq circuit.

    Args:
        circuit: Cirq circuit to convert to a pyQuil Program.

    Returns:
        pyquil.Program object equivalent to the input Cirq circuit.
    """
    if compat:
        circuit = convert_to_contiguous(circuit, rev_qubits=True)
    return Program(to_quil(circuit))


def from_pyquil(program: Program, compat=True) -> Circuit:
    """Returns a Cirq circuit equivalent to the input pyQuil Program.

    Args:
        program: PyQuil Program to convert to a Cirq circuit.

    Returns:
        Cirq circuit representation equivalent to the input pyQuil Program.
    """
    circuit = from_quil(program.out())
    if compat:
        circuit = convert_to_contiguous(circuit, rev_qubits=True)
    return circuit


def from_quil(quil: QuilType) -> Circuit:
    """Returns a Cirq circuit equivalent to the input Quil string.

    Args:
        quil: Quil string to convert to a Cirq circuit.

    Returns:
        Cirq circuit representation equivalent to the input Quil string.
    """
    return circuit_from_quil(quil)
