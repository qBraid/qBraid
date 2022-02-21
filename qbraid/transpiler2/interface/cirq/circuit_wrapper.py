"""CirqCircuitWrapper Class"""

# pylint: disable=invalid-name

from cirq.circuits import Circuit

from qbraid.transpiler2.circuit_wrapper import CircuitWrapper


class CirqCircuitWrapper(CircuitWrapper):
    """Wrapper class for Cirq ``Circuit`` objects."""

    def __init__(self, circuit: Circuit, input_qubit_mapping=None):
        """Create a CirqCircuitWrapper

        Args:
            circuit: the cirq ``Circuit`` object to be wrapped
            input_qubit_mapping (optinal, dict): input qubit mapping

        """
        super().__init__(circuit, input_qubit_mapping)

        self._qubits = circuit.all_qubits()
        self._num_qubits = len(self.qubits)
        self._depth = len(Circuit(circuit.all_operations()))
        self._package = "cirq"
