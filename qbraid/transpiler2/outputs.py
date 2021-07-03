from .cirq.outputs import circuit_to_cirq, instruction_to_cirq, gate_to_cirq
from .qiskit.outputs import circuit_to_qiskit, instruction_to_qiskit, gate_to_qiskit
from .braket.outputs import circuit_to_braket, instruction_to_braket, gate_to_braket

circuit_outputs = {
    "cirq": circuit_to_cirq,
    "qiskit": circuit_to_qiskit,
    "braket": circuit_to_braket,
}

moment_outputs = {}

instruction_outputs = {
    "cirq": instruction_to_cirq,
    "qiskit": instruction_to_qiskit,
    "braket": instruction_to_braket,
}

gate_outputs = {"cirq": gate_to_cirq, "qiskit": gate_to_qiskit, "braket": gate_to_braket}
