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

  * QPROGRAM_REGISTRY: Dict mapping all supported quantum software libraries / package
                         names to their respective program types

"""

from importlib import import_module
from types import ModuleType
from typing import Type


def __dynamic_importer(opt_modules: list[str]) -> list[Type]:
    imported: list = []
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
_PROGRAMS = __dynamic_importer(
    ["cirq", "qiskit", "pennylane", "pyquil", "pytket", "braket.circuits", "openqasm3"]
)

dynamic_type_registry: dict[str, Type] = {t.__module__.split(".")[0]: t for t in _PROGRAMS}
static_type_registry: dict[str, Type] = {"qasm2": str, "qasm3": str}

_QPROGRAM_REGISTRY: dict[str, Type] = dynamic_type_registry | static_type_registry
_QPROGRAM_TYPES: set[Type] = set(_QPROGRAM_REGISTRY.values())
_QPROGRAM_ALIASES: set[str] = set(_QPROGRAM_REGISTRY.keys())
