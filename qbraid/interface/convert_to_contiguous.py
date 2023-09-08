# Copyright (C) 2023 qBraid
#
# This file is part of the qBraid-SDK
#
# The qBraid-SDK is free software released under the GNU General Public License v3
# or later. You can redistribute and/or modify it under the terms of the GPL v3.
# See the LICENSE file in the project root or <https://www.gnu.org/licenses/gpl-3.0.html>.
#
# THERE IS NO WARRANTY for the qBraid-SDK, as per Section 15 of the GPL v3.

"""
Module for converting quantum circuit/program to use contiguous qubit indexing

"""
from typing import TYPE_CHECKING, Any, Callable

from qbraid._qprogram import QPROGRAM
from qbraid.exceptions import ProgramTypeError, QasmError, QbraidError
from qbraid.qasm_checks import get_qasm_version

if TYPE_CHECKING:
    import qbraid


class ContiguousConversionError(QbraidError):
    """Class for exceptions raised while converting a circuit to use contiguous qubits/indices"""


# todo: move to qbraid.passes
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

    if isinstance(program, str):
        try:
            package = get_qasm_version(program)
        except QasmError as err:
            raise ProgramTypeError(
                "Input of type string must represent a valid OpenQASM program."
            ) from err
    else:
        try:
            package = program.__module__
        except AttributeError as err:
            raise ProgramTypeError(program) from err

    # pylint: disable=import-outside-toplevel

    if "pyquil" in package:
        return program

    if "qiskit" in package:
        from qbraid.interface.qbraid_qiskit.tools import _convert_to_contiguous_qiskit

        conversion_function = _convert_to_contiguous_qiskit
    elif "cirq" in package:
        from qbraid.interface.qbraid_cirq.tools import _convert_to_contiguous_cirq

        conversion_function = _convert_to_contiguous_cirq
    elif "braket" in package:
        from qbraid.interface.qbraid_braket.tools import _convert_to_contiguous_braket

        conversion_function = _convert_to_contiguous_braket
    elif "pytket" in package:
        from qbraid.interface.qbraid_pytket.tools import _convert_to_contiguous_pytket

        conversion_function = _convert_to_contiguous_pytket
    elif package == "qasm2":
        from qbraid.interface.qbraid_qasm.tools import _convert_to_contiguous_qasm

        conversion_function = _convert_to_contiguous_qasm
    elif package == "qasm3":
        from qbraid.interface.qbraid_qasm3.tools import _convert_to_contiguous_qasm3

        conversion_function = _convert_to_contiguous_qasm3
    else:
        raise ProgramTypeError(program)

    try:
        compat_program = conversion_function(program, **kwargs)
    except Exception as err:
        raise ContiguousConversionError(
            f"Could not convert {type(program)} to use contiguous qubits/indicies."
        ) from err

    return compat_program
