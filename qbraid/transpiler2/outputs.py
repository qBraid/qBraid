from .cirq.outputs import circuit_to_cirq, instruction_to_cirq
from .qiskit.outputs import circuit_to_qiskit, instruction_to_qiskit
from .braket.outputs import circuit_to_braket, instruction_to_braket

circuit_outputs = {
    'cirq': circuit_to_cirq,
    'qiskit': circuit_to_qiskit,
    'braket': circuit_to_braket,
}

moment_outputps = {}

instruction_outputs = {
    'cirq': instruction_to_cirq,
    'qiskit': instruction_to_qiskit,
    'braket': instruction_to_braket,
}