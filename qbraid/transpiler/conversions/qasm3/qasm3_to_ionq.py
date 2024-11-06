# Copyright (C) 2024 qBraid
#
# This file is part of the qBraid-SDK
#
# The qBraid-SDK is free software released under the GNU General Public License v3
# or later. You can redistribute and/or modify it under the terms of the GPL v3.
# See the LICENSE file in the project root or <https://www.gnu.org/licenses/gpl-3.0.html>.
#
# THERE IS NO WARRANTY for the qBraid-SDK, as per Section 15 of the GPL v3.

"""
Module containing functions to convert between OpenQASM 3 and IonQ JSON format.

"""
from __future__ import annotations

from typing import TYPE_CHECKING

from qbraid_core._import import LazyLoader

from qbraid._logging import logger
from qbraid.programs.gate_model.ionq import IONQ_NATIVE_GATES
from qbraid.transpiler.annotations import weight
from qbraid.transpiler.conversions.openqasm3.openqasm3_to_ionq import openqasm3_to_ionq
from qbraid.transpiler.exceptions import ProgramConversionError

pyqasm = LazyLoader("pyqasm", globals(), "pyqasm")

if TYPE_CHECKING:
    from qbraid.programs.typer import IonQDictType, Qasm3StringType


@weight(1)
def qasm3_to_ionq(qasm: Qasm3StringType) -> IonQDictType:
    """
    Convert an OpenQASM 3 string to IonQ JSON format.

    Args:
        qasm (Qasm3StringType): The OpenQASM 3 string to convert.

    Returns:
        IonQDictType: IonQ JSON format equivalent to the input OpenQASM 3 string.

    Raises:
        ProgramConversionError: If the conversion fails.
    """
    # pylint: disable=broad-exception-caught
    try:
        return openqasm3_to_ionq(qasm)
    except Exception as err:
        err_msg = str(err) or "Failed to convert OpenQASM 3 to IonQ JSON."
        cache_err = None
        try:
            if not any(gate in qasm for gate in IONQ_NATIVE_GATES):
                module = pyqasm.load(qasm)
                module.unroll()
                return openqasm3_to_ionq(module.unrolled_qasm)
        except (ImportError, ModuleNotFoundError) as import_err:
            cache_err = import_err
        except Exception as pyqasm_err:  # pragma: no cover
            logger.debug("Conversion with pyqasm assistance failed: %s", pyqasm_err)
        if (
            cache_err
            and "Cannot mix native and QIS gates in the same circuit" not in err_msg
            and "Circuits with measurements are not supported by the IonQDictType" not in err_msg
        ):
            err_msg += "." if err_msg and not err_msg.endswith(".") else ""
            err_msg += "" if not err_msg else " "
            err_msg += "Please install the 'ionq' extra to enable program unrolling with pyqasm."
        else:
            cache_err = err
        raise ProgramConversionError(err_msg) from cache_err
    # pylint: enable=broad-exception-caught
