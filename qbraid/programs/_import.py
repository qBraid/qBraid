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
Module defining input / output types for a quantum backend:

  * NATIVE_REGISTRY: Dict mapping all supported quantum software libraries / package
                     names to their respective program types.

"""

from copy import deepcopy
from importlib import import_module
from types import ModuleType
from typing import Any, Type

from .typer import BOUND_QBRAID_META_TYPES, QBRAID_META_TYPES


def _assign_default_type_alias(imported: dict[str, Any], program_type: Type[Any]) -> str:
    """
    Determines a unique alias for the given program type based on its module name.

    Args:
        imported (dict[str, Any]): A dictionary of already imported program type aliases.
        program_type (Type[Any]): The class or type for which to determine the alias.

    Returns:
        str: The determined alias for the program type.

    Raises:
        ValueError: If a unique alias cannot be determined due to duplicates.
    """
    module_name = program_type.__module__
    module_parts = module_name.split(".")
    alias = module_parts[0]

    if alias in imported:
        if len(module_parts) > 1:
            alias = f"{alias}_{module_parts[1]}"
        else:
            alias = f"{alias}_{program_type.__name__.lower()}"

        if alias in imported:
            raise ValueError(f"Duplicate alias {alias}")

    return alias


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
            program_type_alias = _assign_default_type_alias(imported, program_type)
            program_type_alias = data[0] if program_type_alias == "builtins" else program_type_alias
            imported[program_type_alias] = program_type
        except Exception:  # pylint: disable=broad-except
            pass

    return imported


# pylint: disable=undefined-variable
def _get_class(module: str):
    if module == "aqt_connector.models.circuits":
        return aqt_connector.models.circuits.QuantumCircuit  # type: ignore # noqa: F821
    if module == "bloqade.analog.builder.assign":
        return bloqade.analog.builder.assign.BatchAssign  # type: ignore # noqa: F821
    if module == "cirq":
        return cirq.Circuit  # type: ignore # noqa: F821
    if module == "qiskit":
        return qiskit.QuantumCircuit  # type: ignore # noqa: F821
    if module == "braket.ahs":
        return braket.ahs.AnalogHamiltonianSimulation  # type: ignore # noqa: F821
    if module == "braket.circuits":
        return braket.circuits.Circuit  # type: ignore # noqa: F821
    if module == "pennylane":
        return pennylane.tape.QuantumTape  # type: ignore # noqa: F821
    if module == "pyquil":
        return pyquil.Program  # type: ignore # noqa: F821
    if module == "pytket":
        return pytket._tket.circuit.Circuit  # type: ignore # noqa: F821
    if module == "openqasm3":
        return openqasm3.ast.Program  # type: ignore # noqa: F821
    if module == "pyqir":
        return pyqir.Module  # type: ignore # noqa: F821
    if module == "cpp_pyqubo":
        return cpp_pyqubo.Model  # type: ignore # noqa: F821
    if module == "cudaq":
        return cudaq.PyKernel  # type: ignore # noqa: F821
    if module == "qibo":  # pragma: no cover
        return qibo.Circuit  # type: ignore # noqa: F821
    if module == "stim":  # pragma: no cover
        return stim.Circuit  # type: ignore # noqa: F821
    if module == "pulser":
        return pulser.sequence.sequence.Sequence  # type: ignore # noqa: F821
    if module == "pyqpanda3":  # pragma: no cover
        return pyqpanda3.core.QProg  # type: ignore # noqa: F821
    if module == "autoqasm":
        return autoqasm.program.program.Program  # type: ignore # noqa: F821
    if module == "qrisp":
        return qrisp.QuantumCircuit  # type: ignore # noqa: F821
    if module == "qat.core.wrappers.circuit":  # pragma: no cover
        return qat.core.wrappers.circuit.Circuit  # type: ignore # noqa: F821
    if module == "mimiqcircuits":
        return mimiqcircuits.Circuit  # type: ignore # noqa: F821
    raise ValueError(f"Unsupported module '{module}'")


# pylint: enable=undefined-variable

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
        "cpp_pyqubo",
        "cudaq",
        "qrisp",
        "mimiqcircuits",
        "aqt_connector.models.circuits",
    ]
)
dynamic_non_native: dict[str, Type[Any]] = _dynamic_importer(
    [
        "bloqade.analog.builder.assign",
        "qibo",
        "stim",
        "pyqir",
        "pulser",
        "pyqpanda3",
        "autoqasm",
        "qat.core.wrappers.circuit",
    ]
)


def _import_by_alias(entries: dict[str, tuple[str, str]]) -> dict[str, Type[Any]]:
    """Import types registered under an explicit alias, skipping any not installed.

    ``_dynamic_importer`` derives one alias per module, which cannot name two types
    from one package (e.g. openfermion's qubit and fermion operators) or give a type
    an alias other than its module's.
    """
    imported: dict[str, Type[Any]] = {}
    for alias, (module_path, attr_path) in entries.items():
        try:
            obj: Any = import_module(module_path)
            for attr in attr_path.split("."):
                obj = getattr(obj, attr)
        except Exception:  # pylint: disable=broad-except
            continue
        imported[alias] = obj
    return imported


# Operator types: convertible with transpile(), never submittable to a device.
OPERATOR_TYPES: dict[str, tuple[str, str]] = {
    "qiskit_pauli": ("qiskit.quantum_info", "SparsePauliOp"),
    "openfermion_qubit": ("openfermion", "QubitOperator"),
    "cirq_pauli": ("cirq", "PauliSum"),
    "pennylane_pauli": ("pennylane.pauli", "PauliSentence"),
    "braket_observable": ("braket.circuits.observable", "Observable"),
    "cudaq_spin": ("cudaq", "SpinOperator"),
    # The types users usually hold, each feeding its library's canonical form above.
    "cirq_pauli_string": ("cirq", "PauliString"),
    "pennylane_op": ("pennylane.operation", "Operator"),
    "qiskit_observable": ("qiskit.quantum_info", "SparseObservable"),
    "cudaq_spin_term": ("cudaq", "SpinOperatorTerm"),
}
dynamic_operator_registry: dict[str, Type[Any]] = _import_by_alias(OPERATOR_TYPES)

static_type_registry: dict[str, Type[Any]] = {
    metatype.__alias__: metatype.__bound__ for metatype in BOUND_QBRAID_META_TYPES
}
qbraid_meta_type_registry: dict[str, Type[Any]] = {
    metatype.__alias__: metatype for metatype in QBRAID_META_TYPES
}

NATIVE_REGISTRY: dict[str, Type[Any]] = (
    dynamic_type_registry
    | dynamic_operator_registry
    | static_type_registry
    | qbraid_meta_type_registry
)
_QPROGRAM_REGISTRY: dict[str, Type[Any]] = deepcopy(NATIVE_REGISTRY) | dynamic_non_native
_QPROGRAM_TYPES: set[Type[Any]] = set(_QPROGRAM_REGISTRY.values())
_QPROGRAM_ALIASES: set[str] = set(_QPROGRAM_REGISTRY.keys())
