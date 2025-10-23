# Copyright 2025 qBraid
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
Module containing functions to convert between OpenQASM 3 and IonQ JSON format.

"""
from __future__ import annotations

from typing import TYPE_CHECKING

import pyqasm

from qbraid._logging import logger
from qbraid.programs.gate_model.ionq import IONQ_NATIVE_GATES
from qbraid.transpiler.annotations import weight
from qbraid.transpiler.conversions.openqasm3.openqasm3_to_ionq import openqasm3_to_ionq
from qbraid.transpiler.exceptions import ProgramConversionError

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
                module = pyqasm.loads(qasm)
                module.unroll()
                return openqasm3_to_ionq(pyqasm.dumps(module))
        except Exception as pyqasm_err:  # pragma: no cover
            logger.debug("Conversion with pyqasm assistance failed: %s", pyqasm_err)
            cache_err = pyqasm_err
        if cache_err and all(
            msg not in err_msg
            for msg in [
                "Cannot mix native and QIS gates in the same circuit",
                "Circuits with measurements are not supported by the IonQDictType",
            ]
        ):
            err_msg += "." if err_msg and not err_msg.endswith(".") else ""
        else:
            cache_err = err
        raise ProgramConversionError(err_msg) from cache_err
    # pylint: enable=broad-exception-caught
