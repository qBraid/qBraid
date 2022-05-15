"""Module for converting quantum circuit/program to use contiguous qubit indexing"""

from typing import TYPE_CHECKING, Any, Callable

from qbraid._typing import QPROGRAM
from qbraid.exceptions import ProgramTypeError, QbraidError

if TYPE_CHECKING:
    import qbraid


class ContiguousConversionError(QbraidError):
    """Class for exceptions raised while converting a circuit to use contiguous qubits/indices"""


def convert_to_contiguous(program: "qbraid.QPROGRAM", **kwargs) -> "qbraid.QPROGRAM":
    """Checks whether the quantum program uses contiguous qubits/indices,
    and if not, adds identity gates to vacant registers as needed.

    Args:
        program (:data:`~qbraid.QPROGRAM`): Any quantum quantum object supported by qBraid.

    Raises:
        ProgramTypeError: If the input circuit is not supported.
        :class:`~qbraid.interface.ContiguousConversionError`: If qubit indexing
            could not be converted

    Returns:
        :data:`~qbraid.QPROGRAM`: Program of the same type as the input quantum program.

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
