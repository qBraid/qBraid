"""QiskitCircuitWrapper Class"""

from typing import Tuple

from cirq import Circuit

from qiskit.circuit import QuantumCircuit

from qbraid.transpiler.interface.qiskit.conversions import from_qiskit, to_qiskit
from qbraid.transpiler.circuit_wrapper import CircuitWrapper

# Currently not used because support parameterized circuits
from qbraid.transpiler.parameter import ParamID


class QiskitCircuitWrapper(CircuitWrapper):
    """Wrapper class for Qiskit ``Circuit`` objects"""

    def __init__(self, circuit: Circuit):
        """Create a QiskitCircuitWrapper

        Args
            circuit: the qiskit ``Circuit`` object to be wrapped
        """
        super().__init__(circuit)

        self._qubits = circuit.qubits
        self._params = circuit.parameters
        self._num_qubits = circuit.num_qubits
        self._num_clbits = circuit.num_clbits
        self._depth = circuit.depth()
        self._input_param_mapping = {p: ParamID(i, p.name) for i, p in enumerate(self.params)}
        self._package = "qiskit"

    def convert_to_cirq(self, circuit: QuantumCircuit) -> Tuple[Circuit, str]:
        """Converts any valid input circuit to a Cirq circuit.

        Args:
            circuit: A qiskit circuit

        Raises:
            UnsupportedCircuitError: If the input circuit is not supported.

        Returns:
            circuit: Cirq circuit equivalent to input circuit.
            input_circuit_type: Type of input circuit represented by a string.
        """
        cirq_circuit = from_qiskit(circuit)
        return cirq_circuit, self.package

    def convert_from_cirq(self, circuit: Circuit, conversion_type: str) -> QuantumCircuit:
        """Converts a Cirq circuit to a type specified by the conversion type.

        Args:
            circuit: Cirq circuit to convert.
            conversion_type: String specifier for the converted circuit type.
        """
        return to_qiskit(circuit)
