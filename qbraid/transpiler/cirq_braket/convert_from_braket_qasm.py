"""Module for converting Braket circuits to Cirq circuit via OpenQASM"""

import numpy as np
from braket.circuits import Circuit as BKCircuit
from braket.circuits import Instruction as BKInstruction
from braket.circuits import gates as braket_gates
from cirq import Circuit
from cirq.contrib.qasm_import.exception import QasmException

from qbraid.interface import convert_to_contiguous, to_unitary
from qbraid.transpiler.cirq_utils import from_qasm
from qbraid.transpiler.exceptions import CircuitConversionError

QASMType = str


def to_qasm(circuit: BKCircuit) -> QASMType:
    """Converts a `braket.circuits.Circuit` to an OpenQASM string.

    Args:
        circuit: Amazon Braket quantum circuit

    Returns:
        The OpenQASM string equivalent to the circuit

    Example:
        >>> from braket.circuits import Circuit
        >>> circuit = Circuit().h(0).cnot(0,1).cnot(1,2)
        >>> print(circuit)
        T  : |0|1|2|

        q0 : -H-C---
                |
        q1 : ---X-C-
                  |
        q2 : -----X-

        T  : |0|1|2|
        >>> print(circuit_to_qasm(circuit))
        OPENQASM 2.0;
        include "qelib1.inc";

        qreg q[3];

        h q[0];
        cx q[0],q[1];
        cx q[1],q[2];

    """

    # A mapping from Amazon Braket gates to QASM gates
    gates = {
        "cnot": "cx",
        "ccnot": "ccx",
        "i": "id",
        "phaseshift": "p",
        "si": "sdg",
        "ti": "tdg",
        "v": "sx",
        "vi": "sxdg",
    }

    # Including the header
    code = 'OPENQASM 2.0;\ninclude "qelib1.inc";\n\n'

    # Initializing the quantum register
    code += "qreg q[" + str(circuit.qubit_count) + "];\n\n"

    circuit_instr = circuit.instructions
    # Building the QASM codelines by applying gates one at a time
    for ins in circuit_instr:

        # Appending the gate name
        if ins.operator.name.lower() not in gates:
            code += ins.operator.name.lower()
        else:
            code += gates[ins.operator.name.lower()]

        # Appending parameters, if any
        try:
            param = "(" + str(ins.operator.angle) + ") "
        except Exception:  # pylint: disable=broad-except
            param = " "
        code += param

        # Appending the gate targets
        targets = [int(q) for q in ins.target]
        code += f"q[{targets[0]}]"
        for t in range(1, len(targets)):
            code += f", q[{targets[t]}]"
        code += ";\n"

    return code


def _gate_to_matrix_braket(gate: braket_gates.Unitary) -> np.ndarray:
    matrix = gate.to_matrix()
    unitary_gate = braket_gates.Unitary(matrix)
    nqubits = int(np.log2(len(matrix)))
    qubits = list(range(nqubits)) if nqubits > 1 else 0
    circuit = BKCircuit([BKInstruction(unitary_gate, qubits)])
    return to_unitary(circuit)


def unitary_braket_instruction(instr: BKInstruction) -> BKInstruction:
    """Converts a Braket instruction to a unitary gate instruction.

    Args:
        instr: Braket instruction to convert.

    Raises:
        CircuitConversionError: If the instruction cannot be converted
    """
    gate = instr.operator

    try:
        matrix = _gate_to_matrix_braket(gate)
        gate_name = "U" if gate.name is None else gate.name
        return BKInstruction(braket_gates.Unitary(matrix, display_name=gate_name), instr.target)
    except (ValueError, TypeError) as err:
        raise CircuitConversionError(f"Unable to convert the instruction {instr}.") from err


def from_braket(circuit: BKCircuit) -> Circuit:
    """Returns a Cirq circuit equivalent to the input Braket circuit.

    Note: The returned Cirq circuit acts on cirq.LineQubit's with indices equal
    to the qubit indices of the Braket circuit.

    Args:
        circuit: Braket circuit to convert to a Cirq circuit.

    Raises:
        CircuitConversionError: if circuit could not be converted
    """
    compat_circuit = convert_to_contiguous(circuit, rev_qubits=True)
    qasm_str = to_qasm(compat_circuit)
    try:
        return from_qasm(qasm_str)
    except QasmException as err:
        raise CircuitConversionError("Error converting qasm string to Cirq circuit") from err
