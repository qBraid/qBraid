from qbraid.transpiler.braket.instruction import BraketInstructionWrapper
from qbraid.transpiler.cirq.instruction import CirqInstructionWrapper
from qbraid.transpiler.qiskit.instruction import QiskitInstructionWrapper
from qbraid.transpiler.braket.circuit import BraketCircuitWrapper
from qbraid.transpiler.cirq.circuit import CirqCircuitWrapper
from qbraid.transpiler.qiskit.circuit import QiskitCircuitWrapper

circuit_wrappers = {
    "qiskit": QiskitCircuitWrapper,
    "cirq": CirqCircuitWrapper,
    "braket": BraketCircuitWrapper,
}

instruction_wrappers = {
    "qiskit": QiskitInstructionWrapper,
    "cirq": CirqInstructionWrapper,
    "braklet": BraketInstructionWrapper,
}
