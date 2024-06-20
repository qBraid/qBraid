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
Module defining input / output types for a quantum backend:

  * QPROGRAM: Type alias defining all supported quantum circuit / program types

  * NATIVE_REGISTRY: Dict mapping all supported quantum software libraries / package
                         names to their respective program types

"""

from copy import deepcopy
from importlib import import_module
from types import ModuleType
from typing import Any, Type


def _dynamic_importer(opt_modules: list[str]) -> dict[str, Type[Any]]:
    imported: dict[str, Type[Any]] = {}

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
            program_type = _get_class(module.__name__)
            program_module_parts = module.__name__.split(".")
            if program_module_parts[0] == "braket" and program_module_parts[1] == "ahs":
                program_type_alias = "braket_ahs"
            else:
                program_type_alias = program_module_parts[0]
            imported[program_type_alias] = program_type
        except Exception:  # pylint: disable=broad-except
            pass

    return imported


# pylint: disable=undefined-variable,inconsistent-return-statements
def _get_class(module: str):
    if module == "cirq":
        return cirq.Circuit  # type: ignore
    if module == "qiskit":
        return qiskit.QuantumCircuit  # type: ignore
    if module == "braket.ahs":
        return braket.ahs.AnalogHamiltonianSimulation  # type: ignore
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
    if module == "pyqir":
        return pyqir.Module  # type: ignore


# Supported quantum programs.
dynamic_type_registry: dict[str, Type[Any]] = _dynamic_importer(
    [
        "cirq",
        "qiskit",
        "pennylane",
        "pyquil",
        "pytket",
        "braket.circuits",
        "braket.ahs",
        "openqasm3",
        "pyqir",
    ]
)
static_type_registry: dict[str, Type[Any]] = {"qasm2": str, "qasm3": str}

NATIVE_REGISTRY: dict[str, Type[Any]] = dynamic_type_registry | static_type_registry
_QPROGRAM_REGISTRY: dict[str, Type[Any]] = deepcopy(NATIVE_REGISTRY)
_QPROGRAM_TYPES: set[Type[Any]] = set(_QPROGRAM_REGISTRY.values())
_QPROGRAM_ALIASES: set[str] = set(_QPROGRAM_REGISTRY.keys())
