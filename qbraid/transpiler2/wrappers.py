from qbraid.transpiler2.braket.instruction import BraketInstructionWrapper
from qbraid.transpiler2.cirq.instruction import CirqInstructionWrapper
from qbraid.transpiler2.qiskit.instruction import QiskitInstructionWrapper
from qbraid.transpiler2.braket.circuit import BraketCircuitWrapper
from qbraid.transpiler2.cirq.circuit import CirqCircuitWrapper
from qbraid.transpiler2.qiskit.circuit import QiskitCircuitWrapper

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
