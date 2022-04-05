"""Module for converting quantum circuit/program to use contiguous qubit indexing"""

from typing import Any, Callable

from qbraid._typing import QPROGRAM, SUPPORTED_PROGRAM_TYPES
from qbraid.exceptions import UnsupportedProgramError
from qbraid.transpiler.exceptions import CircuitConversionError


def convert_to_contiguous(program: QPROGRAM, **kwargs) -> QPROGRAM:
    """Checks whether the quantum program uses contiguous qubits/indices,
    and if not, adds identity gates to vacant registers as needed.
    Args:
        program: Any quantum quantum object supported by qBraid.
    Raises:
        UnsupportedProgramError: If the input circuit is not supported.
    Returns:
        QPROGRAM: Program of the same type as the input quantum program.
    """
    conversion_function: Callable[[Any], QPROGRAM]

    try:
        package = program.__module__
    except AttributeError as err:
        raise UnsupportedProgramError(
            "Could not determine the package of the input quantum program."
        ) from err

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
        raise UnsupportedProgramError(
            f"Quantum program from module {package} is not supported.\n\n"
            f"Quantum program types supported by qBraid are \n{SUPPORTED_PROGRAM_TYPES}"
        )

    try:
        compat_program = conversion_function(program, **kwargs)
    except Exception as err:
        raise CircuitConversionError(
            "Could not convert given quantum program to use contiguous qubits/indicies."
        ) from err

    return compat_program
