"""Transpiler utils module"""

from .braket_utils import (
    circuit_to_braket,
    create_braket_gate,
    gate_to_braket,
    get_braket_gate_data,
    instruction_to_braket,
)
from .cirq_utils import (
    circuit_to_cirq,
    create_cirq_gate,
    gate_to_cirq,
    get_cirq_gate_data,
    instruction_to_cirq,
    int_from_qubit,
    moment_to_cirq,
)
from .qiskit_utils import (
    circuit_to_qiskit,
    create_qiskit_gate,
    gate_to_qiskit,
    get_qiskit_gate_data,
    instruction_to_qiskit,
)

supported_packages = {
    "cirq": ["braket", "qiskit", "qbraid"],
    "qiskit": ["braket", "cirq", "qbraid"],
    "braket": ["qiskit", "cirq", "qbraid"],
    "qbraid": ["cirq", "braket", "qiskit"],
}

circuit_outputs = {
    "cirq": circuit_to_cirq,
    "qiskit": circuit_to_qiskit,
    "braket": circuit_to_braket,
}

moment_outputs = {
    "cirq": moment_to_cirq,
}

instruction_outputs = {
    "cirq": instruction_to_cirq,
    "qiskit": instruction_to_qiskit,
    "braket": instruction_to_braket,
}

gate_outputs = {"cirq": gate_to_cirq, "qiskit": gate_to_qiskit, "braket": gate_to_braket}
