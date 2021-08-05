from .braket_utils import (
    get_braket_gate_data,
    create_braket_gate,
    circuit_to_braket,
    instruction_to_braket,
    gate_to_braket,
)

from .cirq_utils import (
    get_cirq_gate_data,
    create_cirq_gate,
    circuit_to_cirq,
    moment_to_cirq,
    instruction_to_cirq,
    gate_to_cirq,
)

from .qiskit_utils import (
    get_qiskit_gate_data,
    create_qiskit_gate,
    circuit_to_qiskit,
    instruction_to_qiskit,
    gate_to_qiskit,
)

supported_packages = {
    "cirq": ["braket", "qiskit", "qbraid"],
    "qiskit": ["braket", "cirq", "qbraid"],
    "braket": ["qiskit", "cirq", "qbraid"],
    "qbraid": ["cirq","braket","qiskit"]
}

circuit_outputs = {
    "cirq": circuit_to_cirq,
    "qiskit": circuit_to_qiskit,
    "braket": circuit_to_braket,
}

moment_outputs = {
    'cirq': moment_to_cirq,
}

instruction_outputs = {
    "cirq": instruction_to_cirq,
    "qiskit": instruction_to_qiskit,
    "braket": instruction_to_braket,
}

gate_outputs = {"cirq": gate_to_cirq, "qiskit": gate_to_qiskit, "braket": gate_to_braket}
