from typing import Optional

import cirq
from cirq import circuits, ops

from qbraid.transpiler.interface.qasm_output import QasmOutput

QASMType = str


def _to_qasm_output(
    circuit: circuits.Circuit,
    header: Optional[str] = None,
    precision: int = 10,
    qubit_order: "cirq.QubitOrderOrList" = ops.QubitOrder.DEFAULT,
) -> QasmOutput:
    """Returns a QASM object equivalent to the circuit.
    Args:
        header: A multi-line string that is placed in a comment at the top
            of the QASM. Defaults to a cirq version specifier.
        precision: Number of digits to use when representing numbers.
        qubit_order: Determines how qubits are ordered in the QASM
            register.
    """
    if header is None:
        header = f"Generated from Cirq v{cirq._version.__version__}"
    qubits = ops.QubitOrder.as_qubit_order(qubit_order).order_for(circuit.all_qubits())
    return QasmOutput(
        operations=circuit.all_operations(),
        qubits=qubits,
        header=header,
        precision=precision,
        version="2.0",
    )


def circuit_to_qasm(
    circuit: circuits.Circuit,
    header: Optional[str] = None,
    precision: int = 10,
    qubit_order: "cirq.QubitOrderOrList" = ops.QubitOrder.DEFAULT,
) -> QASMType:
    """Converts a `cirq.Circuit` to an OpenQASM string.
    Args:
        circuit: cirq Circuit object
        header: A multi-line string that is placed in a comment at the top
            of the QASM. Defaults to a cirq version specifier.
        precision: Number of digits to use when representing numbers.
        qubit_order: Determines how qubits are ordered in the QASM
            register.
    """

    return str(_to_qasm_output(circuit, header, precision, qubit_order))
