"""BraketCircuitWrapper Class"""

from braket.circuits.circuit import Circuit as BKCircuit

from qbraid.transpiler.wrappers.abc_qprogram import QuantumProgramWrapper


class BraketCircuitWrapper(QuantumProgramWrapper):
    """Wrapper class for Amazon Braket ``Circuit`` objects."""

    def __init__(self, circuit: BKCircuit):
        """Create a BraketCircuitWrapper

        Args:
            circuit: the circuit object to be wrapped

        """
        super().__init__(circuit)

        self._qubits = circuit.qubits
        self._num_qubits = len(self.qubits)
        self._depth = circuit.depth
        self._package = "braket"
        self._program_type = "Circuit"
