"""CirqCircuitWrapper Class"""

# pylint: disable=invalid-name

from typing import Tuple, Callable

from cirq.circuits import Circuit

from qbraid._typing import QPROGRAM, SUPPORTED_PROGRAM_TYPES
from qbraid.exceptions import UnsupportedCircuitError
from qbraid.transpiler2.exceptions import CircuitConversionError
from qbraid.transpiler2.wrapper_abc import CircuitWrapper


class CirqCircuitWrapper(CircuitWrapper):
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

    def convert_to_cirq(self, circuit: Circuit) -> Tuple[Circuit, str]:
        """Converts any valid input circuit to a Cirq circuit.

        Args:
            circuit: A Cirq circuit

        Raises:
            UnsupportedCircuitError: If the input circuit is not supported.

        Returns:
            circuit: Cirq circuit equivalent to input circuit.
            input_circuit_type: Type of input circuit represented by a string.
        """
        return circuit, self.package

    def convert_from_cirq(circuit: Circuit, conversion_type: str) -> QPROGRAM:
        """Converts a Cirq circuit to a type specified by the conversion type.

        Args:
            circuit: Cirq circuit to convert.
            conversion_type: String specifier for the converted circuit type.
        """
        conversion_function: Callable[[Circuit], QPROGRAM]
        if conversion_type == "qiskit":
            from qbraid.transpiler.interface.qiskit.conversions import to_qiskit

            conversion_function = to_qiskit
        elif conversion_type == "pyquil":
            from qbraid.transpiler.interface.pyquil.conversions import to_pyquil

            conversion_function = to_pyquil
        elif conversion_type == "braket":
            from qbraid.transpiler.interface.braket.convert_to_braket import to_braket

            conversion_function = to_braket
        elif conversion_type == "pennylane":
            from qbraid.transpiler.interface.pennylane.conversions import to_pennylane

            conversion_function = to_pennylane
        elif conversion_type == "cirq":

            def conversion_function(circ: Circuit) -> Circuit:
                return circ

        else:
            raise UnsupportedCircuitError(
                f"Conversion to circuit of type {conversion_type} is "
                "unsupported. \nCircuit types supported by the "
                f"qbraid.transpiler = {SUPPORTED_PROGRAM_TYPES}"
            )
        try:
            converted_circuit = conversion_function(circuit)
        except Exception:
            raise CircuitConversionError(
                f"Circuit could not be converted from a Cirq type to a "
                f"circuit of type {conversion_type}."
            )

        return converted_circuit
