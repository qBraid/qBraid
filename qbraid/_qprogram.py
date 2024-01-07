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
Module defining input / output types for a quantum backend:

  * QPROGRAM: Type alias defining all supported quantum circuit / program types

  * SUPPORTED_QPROGRAMS: Dict mapping all supported quantum software libraries / package
                         names to their respective program types

"""

from importlib import import_module
from types import ModuleType
from typing import List, Union

__NON_OPTIONAL_PROGRAMS: list = []

# As we are using here dynamic imports, we'll see the ide will visualize that none of the
# libraries have been import, as we'll import them dynamically in the execution.


def __dynamic_importer(opt_modules: List[str]) -> list:
    imported: list = __NON_OPTIONAL_PROGRAMS
    for m in opt_modules:
        try:
            data = m.split(".")
            for i, _ in enumerate(data):
                if data[:i]:
                    globals()[".".join(data[:i])] = import_module(".".join(data[:i]))
            # to be more secure, do not do module = globals()[m] = import_module(), as it could
            # create globals()[m] and later throw an error as there is no module named like that.
            # Is prefered to let module be import_module() and throw an exception if is needed
            module: ModuleType = import_module(m)
            globals()[m] = module
            imported.append(__get_class(module.__name__))
        except Exception:  # pylint: disable=broad-except
            pass
    return imported


# pylint: disable=undefined-variable,inconsistent-return-statements
def __get_class(module: str):
    if module == "cirq":
        return cirq.Circuit  # type: ignore
    if module == "qiskit":
        return qiskit.QuantumCircuit  # type: ignore
    if module == "braket.circuits":
        return braket.circuits.Circuit  # type: ignore
    if module == "pennylane":
        return pennylane.tape.QuantumTape  # type: ignore
    if module == "pyquil":
        return pyquil.Program  # type: ignore
    if module == "pytket":
        return pytket._tket.circuit.Circuit  # type: ignore
    if module == "openqasm3":
        return openqasm3.ast.Program  # type: ignore


# Supported quantum programs.
QASMType = str
_PROGRAMS = __dynamic_importer(
    ["cirq", "qiskit", "pennylane", "pyquil", "pytket", "braket.circuits", "openqasm3"]
)
QPROGRAM = Union[tuple(_PROGRAMS)]  # type: ignore

# pylint: disable-next=bad-str-strip-call
_PROGRAM_TYPES = [str(x).strip("<class").strip(">").strip(" ").strip("'") for x in _PROGRAMS]
QPROGRAM_TYPES = _PROGRAMS + [QASMType]

_PROGRAM_LIBS = [x.split(".")[0] for x in _PROGRAM_TYPES]
SUPPORTED_QPROGRAMS = dict(zip(_PROGRAM_LIBS, _PROGRAM_TYPES)) | {"qasm2": "str", "qasm3": "str"}
QPROGRAM_LIBS = list(SUPPORTED_QPROGRAMS.keys())
