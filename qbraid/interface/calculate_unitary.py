"""Module for calculating unitary of quantum circuit/program"""

from typing import Any, Callable

import numpy as np

from qbraid._typing import QPROGRAM, SUPPORTED_PROGRAM_TYPES
from qbraid.exceptions import QbraidError, UnsupportedCircuitError
from qbraid.interface.convert_to_contiguous import convert_to_contiguous


class UnitaryCalculationError(QbraidError):
    """Class for exceptions raised during unitary calculation"""


def to_unitary(circuit: QPROGRAM, ensure_contiguous=False) -> np.ndarray:
    """Calculates the unitary of any valid input circuit.
    Args:
        circuit: Any quantum circuit object supported by qBraid.
        ensure_contiguous: If True, calculates unitary using contiguous qubit indexing
    Raises:
        UnsupportedCircuitError: If the input circuit is not supported.
    Returns:
        numpy.ndarray: Matrix representation of the input circuit.
    """
    to_unitary_function: Callable[[Any], np.ndarray]

    try:
        package = circuit.__module__
    except AttributeError as err:
        raise UnsupportedCircuitError(
            "Could not determine the package of the input circuit."
        ) from err

    # pylint: disable=import-outside-toplevel

    if "qiskit" in package:
        from qbraid.interface.qbraid_qiskit.utils import _unitary_from_qiskit

        to_unitary_function = _unitary_from_qiskit
    elif "cirq" in package:
        from qbraid.interface.qbraid_cirq.utils import _unitary_from_cirq

        to_unitary_function = _unitary_from_cirq
    elif "braket" in package:
        from qbraid.interface.qbraid_braket.utils import _unitary_from_braket

        to_unitary_function = _unitary_from_braket
    else:
        raise UnsupportedCircuitError(
            f"Circuit from module {package} is not supported.\n\n"
            f"Circuit types supported by qBraid are \n{SUPPORTED_PROGRAM_TYPES}"
        )

    circuit_input = convert_to_contiguous(circuit) if ensure_contiguous else circuit

    try:
        unitary = to_unitary_function(circuit_input)
    except Exception as err:
        raise UnitaryCalculationError(
            "Unitary could not be calculated from given circuit."
        ) from err

    return unitary


def equal_unitaries(circuit_0: QPROGRAM, circuit_1: QPROGRAM) -> bool:
    """Returns True if input circuit unitaries are equivalent."""
    unitary_0 = to_unitary(circuit_0, ensure_contiguous=True)
    unitary_1 = to_unitary(circuit_1, ensure_contiguous=True)
    return np.allclose(unitary_0, unitary_1)
