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
Module containing top-level qbraid wrapper functionality. Each of these
functions utilize entrypoints via ``pkg_resources``.

"""
import warnings

import openqasm3

from qbraid._import import _load_entrypoint
from qbraid.exceptions import QbraidError

from ._qprogram import QPROGRAM
from .inspector import get_program_type


def circuit_wrapper(program: QPROGRAM):
    """Apply qbraid quantum program wrapper to a supported quantum program.

    This function is used to create a qBraid :class:`~qbraid.transpiler.QuantumProgram`
    object, which can then be transpiled to any supported quantum circuit-building package.
    The input quantum circuit object must be an instance of a circuit object derived from a
    supported package.

    .. code-block:: python

        cirq_circuit = cirq.Circuit()
        q0, q1, q2 = [cirq.LineQubit(i) for i in range(3)]
        ...

    Please refer to the documentation of the individual qbraid circuit wrapper objects to see
    any additional arguments that might be supported.

    Args:
        circuit (:data:`~qbraid.QPROGRAM`): A supported quantum circuit / program object

    Returns:
        :class:`~qbraid.transpiler.QuantumProgram`: A wrapped quantum circuit-like object

    Raises:
        :class:`~qbraid.QbraidError`: If the input circuit is not a supported quantum program.

    """
    warnings.warn(
        "qbraid.programs.circuit_wrapper() is deprecated. Please use \
        qbraid.programs.loads instead.",
        PendingDeprecationWarning,
    )
    if isinstance(program, openqasm3.ast.Program):
        program = openqasm3.dumps(program)

    try:
        package = get_program_type(program)
    except QbraidError as err:
        raise QbraidError(
            f"Error applying circuit wrapper to quantum program \
            of type {type(program)}"
        ) from err

    try:
        circuit_wrapper_class = _load_entrypoint("programs", package)
    except Exception as err:
        raise QbraidError(
            f"Error applying circuit wrapper to quantum program of type {type(program)}"
        ) from err

    return circuit_wrapper_class(program)
