"""CirqCircuitWrapper Class"""

# pylint: disable=invalid-name

from cirq.circuits import Circuit

from qbraid.transpiler.wrapper_abc import QuantumProgramWrapper


class CirqCircuitWrapper(QuantumProgramWrapper):
    """Wrapper class for Cirq ``Circuit`` objects."""

    def __init__(self, circuit: Circuit):
        """Create a CirqCircuitWrapper

        Args:
            circuit: the cirq ``Circuit`` object to be wrapped

        """
        super().__init__(circuit)

        self._qubits = circuit.all_qubits()
        self._num_qubits = len(self.qubits)
        self._depth = len(Circuit(circuit.all_operations()))
        self._package = "cirq"
        self._program_type = "Circuit"
