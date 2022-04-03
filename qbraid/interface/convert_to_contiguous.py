"""Module for converting quantum circuit/program to use contiguous qubit indexing"""

from typing import Any, Callable

from qbraid._typing import QPROGRAM, SUPPORTED_PROGRAM_TYPES
from qbraid.exceptions import UnsupportedCircuitError
from qbraid.transpiler.exceptions import CircuitConversionError

# pylint: disable=import-outside-toplevel,duplicate-code


def convert_to_contiguous(circuit: QPROGRAM, **kwargs) -> QPROGRAM:
    """Checks whether the circuit uses contiguous qubits/indices,
    and if not, adds identity gates to vacant registers as needed.

    Args:
        circuit: Any quantum circuit object supported by qBraid.

    Raises:
        UnsupportedCircuitError: If the input circuit is not supported.

    Returns:
        QPROGRAM: Circuit object of the same type as the input circuit.
    """
    conversion_function: Callable[[Any], QPROGRAM]

    try:
        package = circuit.__module__
    except AttributeError as err:
        raise UnsupportedCircuitError(
            "Could not determine the package of the input circuit."
        ) from err

    if "qiskit" in package:
        return circuit

    if "cirq" in package:
        from qbraid.interface.qbraid_cirq.contiguous import _convert_to_contiguous_cirq

        conversion_function = _convert_to_contiguous_cirq
    elif "braket" in package:
        from qbraid.interface.qbraid_braket.contiguous import _convert_to_contiguous_braket

        conversion_function = _convert_to_contiguous_braket
    else:
        raise UnsupportedCircuitError(
            f"Circuit from module {package} is not supported.\n\n"
            f"Circuit types supported by qBraid are \n{SUPPORTED_PROGRAM_TYPES}"
        )

    try:
        compat_circuit = conversion_function(circuit, **kwargs)
    except Exception as err:
        raise CircuitConversionError(
            "Could not convert given circuit to use contiguous qubits/indicies."
        ) from err

    return compat_circuit
