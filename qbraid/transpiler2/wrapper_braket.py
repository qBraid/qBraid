"""BraketCircuitWrapper Class"""

from typing import Tuple

from braket.circuits.circuit import Circuit as BKCircuit
from cirq import Circuit as CirqCircuit

from qbraid.transpiler2.wrapper_abc import CircuitWrapper
from qbraid.transpiler2.cirq_braket.convert_from_braket import from_braket
from qbraid.transpiler2.cirq_braket.convert_to_braket import to_braket


class BraketCircuitWrapper(CircuitWrapper):
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

    def convert_to_cirq(self, circuit: BKCircuit) -> Tuple[CirqCircuit, str]:
        """Converts any valid input circuit to a Cirq circuit.

        Args:
            circuit: A braket circuit

        Raises:
            UnsupportedCircuitError: If the input circuit is not supported.

        Returns:
            circuit: Cirq circuit equivalent to input circuit.
            input_circuit_type: Type of input circuit represented by a string.
        """
        cirq_circuit = from_braket(circuit)
        return cirq_circuit, self.package

    def convert_from_cirq(self, circuit: CirqCircuit, conversion_type: str) -> BKCircuit:
        """Converts a Cirq circuit to a type specified by the conversion type.

        Args:
            circuit: Cirq circuit to convert.
            conversion_type: String specifier for the converted circuit type.
        """
        return to_braket(circuit)
