# Copyright 2023 qBraid
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Module for converting quantum circuit/program to use contiguous qubit indexing

"""
from typing import TYPE_CHECKING, Any, Callable

from qbraid._qprogram import QPROGRAM
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
    else:
        raise ProgramTypeError(program)

    try:
        compat_program = conversion_function(program, **kwargs)
    except Exception as err:
        raise ContiguousConversionError(
            f"Could not convert {type(program)} to use contiguous qubits/indicies."
        ) from err

    return compat_program
