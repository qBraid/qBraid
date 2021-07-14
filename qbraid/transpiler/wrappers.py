from .braket.circuit import BraketCircuitWrapper
from .braket.instruction import BraketInstructionWrapper
from .cirq.circuit import CirqCircuitWrapper
from .cirq.instruction import CirqInstructionWrapper
from .qiskit.circuit import QiskitCircuitWrapper
from .qiskit.instruction import QiskitInstructionWrapper

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
