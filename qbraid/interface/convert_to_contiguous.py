"""Module for converting quantum circuit/program to use contiguous qubit indexing"""

from typing import Any, Callable

from qbraid._typing import QPROGRAM
from qbraid.exceptions import ProgramTypeError, QbraidError


class ContiguousConversionError(QbraidError):
    """Class for exceptions raised while converting a circuit to use contiguous qubits/indices"""


def convert_to_contiguous(program: QPROGRAM, **kwargs) -> QPROGRAM:
    """Checks whether the quantum program uses contiguous qubits/indices,
    and if not, adds identity gates to vacant registers as needed.

    Args:
        program: Any quantum quantum object supported by qBraid.
    Raises:
        ProgramTypeError: If the input circuit is not supported.
    Returns:
        QPROGRAM: Program of the same type as the input quantum program.
    """
    conversion_function: Callable[[Any], QPROGRAM]

    try:
        package = program.__module__
    except AttributeError as err:
        raise ProgramTypeError(program) from err

    # pylint: disable=import-outside-toplevel

    if "qiskit" in package:
        return program

    if "pyquil" in package:
        return program

    if "pennylane" in package:
        return program

    if "cirq" in package:
        from qbraid.interface.qbraid_cirq.tools import _convert_to_contiguous_cirq

        conversion_function = _convert_to_contiguous_cirq
    elif "braket" in package:
        from qbraid.interface.qbraid_braket.tools import _convert_to_contiguous_braket

        conversion_function = _convert_to_contiguous_braket
    else:
        raise ProgramTypeError(program)

    try:
        compat_program = conversion_function(program, **kwargs)
    except Exception as err:
        raise ContiguousConversionError(
            f"Could not convert {type(program)} to use contiguous qubits/indicies."
        ) from err

    return compat_program
