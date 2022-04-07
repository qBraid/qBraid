"""Module for calculating unitary of quantum circuit/program"""

from typing import Any, Callable

import numpy as np

from qbraid._typing import QPROGRAM
from qbraid.exceptions import ProgramTypeError, QbraidError
from qbraid.interface.convert_to_contiguous import convert_to_contiguous


class UnitaryCalculationError(QbraidError):
    """Class for exceptions raised during unitary calculation"""


def to_unitary(program: QPROGRAM, ensure_contiguous=False) -> np.ndarray:
    """Calculates the unitary of any valid input quantum program.

    Args:
        program: Any quantum program object supported by qBraid.
        ensure_contiguous: If True, calculates unitary using contiguous qubit indexing
    Raises:
        ProgramTypeError: If the input quantum program is not supported.
    Returns:
        numpy.ndarray: Matrix representation of the input quantum program.
    """
    to_unitary_function: Callable[[Any], np.ndarray]

    try:
        package = program.__module__
    except AttributeError as err:
        raise ProgramTypeError(program) from err

    # pylint: disable=import-outside-toplevel

    if "qiskit" in package:
        from qbraid.interface.qbraid_qiskit.tools import _unitary_from_qiskit

        to_unitary_function = _unitary_from_qiskit
    elif "cirq" in package:
        from qbraid.interface.qbraid_cirq.tools import _unitary_from_cirq

        to_unitary_function = _unitary_from_cirq
    elif "braket" in package:
        from qbraid.interface.qbraid_braket.tools import _unitary_from_braket

        to_unitary_function = _unitary_from_braket
    elif "pyquil" in package:
        from qbraid.interface.qbraid_pyquil.tools import _unitary_from_pyquil

        to_unitary_function = _unitary_from_pyquil
    elif "pennylane" in package:
        from qbraid.interface.qbraid_pennylane.tools import _unitary_from_pennylane

        to_unitary_function = _unitary_from_pennylane
    else:
        raise ProgramTypeError(program)

    program_input = convert_to_contiguous(program) if ensure_contiguous else program

    try:
        unitary = to_unitary_function(program_input)
    except Exception as err:
        raise UnitaryCalculationError(
            "Unitary could not be calculated from given quantum program."
        ) from err

    return unitary


def equal_unitaries(program_0: QPROGRAM, program_1: QPROGRAM) -> bool:
    """Returns True if input quantum program unitaries are equivalent."""
    unitary_0 = to_unitary(program_0, ensure_contiguous=True)
    unitary_1 = to_unitary(program_1, ensure_contiguous=True)
    return np.allclose(unitary_0, unitary_1)
