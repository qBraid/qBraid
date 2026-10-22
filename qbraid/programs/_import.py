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

Optional quantum SDKs are registered lazily. An alias is listed as soon as its package
is installed, but the package itself is only imported the first time its program type
is looked up. This keeps ``import qbraid.programs`` from paying the import cost of
every installed SDK.

"""
from __future__ import annotations

import copy as _copy
import importlib.util
import sys
import threading
from collections.abc import (
    Callable,
    ItemsView,
    Iterable,
    Iterator,
    Mapping,
    MutableMapping,
    MutableSet,
    ValuesView,
)
from importlib import import_module
from importlib.machinery import PathFinder
from typing import Any, NamedTuple, Optional, Type

from qbraid._logging import logger

from .typer import BOUND_QBRAID_META_TYPES, QBRAID_META_TYPES


class _LazyType(NamedTuple):
    """Reference to a program type that has not been imported yet."""

    module: str
    attr: str


# alias -> (module to import, attribute path on that module)
_NATIVE_LAZY_TYPES: dict[str, _LazyType] = {
    "cirq": _LazyType("cirq", "Circuit"),
    "qiskit": _LazyType("qiskit", "QuantumCircuit"),
    "pennylane": _LazyType("pennylane", "tape.QuantumTape"),
    "pyquil": _LazyType("pyquil", "Program"),
    "pytket": _LazyType("pytket", "_tket.circuit.Circuit"),
    "braket": _LazyType("braket.circuits", "Circuit"),
    "braket_ahs": _LazyType("braket.ahs", "AnalogHamiltonianSimulation"),
    "openqasm3": _LazyType("openqasm3", "ast.Program"),
    "cpp_pyqubo": _LazyType("cpp_pyqubo", "Model"),
    "cudaq": _LazyType("cudaq", "PyKernel"),
    "qrisp": _LazyType("qrisp", "QuantumCircuit"),
    "mimiqcircuits": _LazyType("mimiqcircuits", "Circuit"),
    "aqt_connector": _LazyType("aqt_connector.models.circuits", "QuantumCircuit"),
}

_NON_NATIVE_LAZY_TYPES: dict[str, _LazyType] = {
    "bloqade": _LazyType("bloqade.analog.builder.assign", "BatchAssign"),
    "qibo": _LazyType("qibo", "Circuit"),
    "stim": _LazyType("stim", "Circuit"),
    "pyqir": _LazyType("pyqir", "Module"),
    "pulser": _LazyType("pulser", "sequence.sequence.Sequence"),
    "pyqpanda3": _LazyType("pyqpanda3", "core.QProg"),
    "autoqasm": _LazyType("autoqasm", "program.program.Program"),
    "qat": _LazyType("qat.core.wrappers.circuit", "Circuit"),
}


def _module_available(name: str) -> bool:
    """Check whether a module can be imported, without importing it or its parents.

    ``importlib.util.find_spec`` imports parent packages for dotted names, which is
    exactly the cost this module avoids, so submodules are located with ``PathFinder``.
    """
    if name in sys.modules:
        return True

    root, _, rest = name.partition(".")
    try:
        spec = importlib.util.find_spec(root)
    except (ImportError, ValueError):
        return False

    path = root
    for part in rest.split(".") if rest else []:
        if spec is None or spec.submodule_search_locations is None:
            return False
        path = f"{path}.{part}"
        spec = PathFinder.find_spec(path, list(spec.submodule_search_locations))

    return spec is not None


def _load_type(ref: _LazyType) -> Type[Any]:
    obj: Any = import_module(ref.module)
    for part in ref.attr.split("."):
        obj = getattr(obj, part)
    return obj


class LazyTypeRegistry(MutableMapping):
    """Alias to program type mapping that imports optional SDKs on first lookup.

    Membership checks and key iteration never import anything. Looking up a value
    imports the SDK that defines it. If that import fails, the alias is dropped
    with a warning instead of failing silently.
    """

    def __init__(self, data: Optional[Mapping[str, Any]] = None):
        self._data: dict[str, Any] = dict(data or {})
        self._lock = threading.RLock()
        self._drop_callbacks: list[Callable[[str], None]] = []

    def _resolve(self, alias: str) -> Type[Any]:
        value = self._data[alias]
        if not isinstance(value, _LazyType):
            return value

        with self._lock:
            try:
                program_type = _load_type(value)
            except Exception as err:  # pylint: disable=broad-exception-caught
                logger.warning(
                    "Dropping program type alias '%s': failed to load '%s.%s' (%s: %s)",
                    alias,
                    value.module,
                    value.attr,
                    type(err).__name__,
                    err,
                )
                self._data.pop(alias, None)
                for callback in self._drop_callbacks:
                    callback(alias)
                raise KeyError(alias) from err
            self._data[alias] = program_type
            return program_type

    def __getitem__(self, alias: str) -> Type[Any]:
        return self._resolve(alias)

    def __setitem__(self, alias: str, program_type: Type[Any]) -> None:
        self._data[alias] = program_type

    def __delitem__(self, alias: str) -> None:
        del self._data[alias]

    def __contains__(self, alias: object) -> bool:
        return alias in self._data

    def __iter__(self) -> Iterator[str]:
        return iter(list(self._data))

    def __len__(self) -> int:
        return len(self._data)

    def __repr__(self) -> str:
        return f"{type(self).__name__}({self._data!r})"

    def items(self) -> ItemsView:
        return _ResolvedItemsView(self)

    def values(self) -> ValuesView:
        return _ResolvedValuesView(self)

    def clear(self) -> None:
        self._data.clear()

    def copy(self) -> LazyTypeRegistry:
        """Return a shallow copy that keeps unresolved entries unresolved."""
        return type(self)(self._data)

    __copy__ = copy

    def __deepcopy__(self, memo: dict) -> LazyTypeRegistry:
        return type(self)(_copy.deepcopy(self._data, memo))

    def __reduce__(self):
        return (type(self), (dict(self._data),))

    def __or__(self, other: Mapping) -> LazyTypeRegistry:
        if not isinstance(other, Mapping):
            return NotImplemented
        merged = self.copy()
        merged.update(other)
        return merged

    def __ror__(self, other: Mapping) -> LazyTypeRegistry:
        if not isinstance(other, Mapping):
            return NotImplemented
        merged = type(self)(other)
        merged.update(self)
        return merged

    def __ior__(self, other: Mapping) -> LazyTypeRegistry:
        self.update(other)
        return self

    def update(self, other=(), /, **kwargs) -> None:  # pylint: disable=arguments-differ
        if isinstance(other, LazyTypeRegistry):
            self._data.update(other._data)
            other = ()
        super().update(other, **kwargs)

    def is_loaded(self, alias: str) -> bool:
        """Return True if the program type for ``alias`` has already been imported."""
        return alias in self._data and not isinstance(self._data[alias], _LazyType)

    def loaded_items(self) -> Iterator[tuple[str, Type[Any]]]:
        """Yield the entries whose defining module has already been imported.

        An object can only be an instance of a registered type if the module that
        defines that type is already imported, so type checks on a given program
        never need to look beyond these entries.
        """
        for alias, value in list(self._data.items()):
            if isinstance(value, _LazyType):
                if value.module not in sys.modules:
                    continue
                try:
                    value = self._resolve(alias)
                except KeyError:
                    continue
            yield alias, value

    def on_drop(self, callback: Callable[[str], None]) -> None:
        """Register a callback invoked with the alias of an entry that failed to load."""
        self._drop_callbacks.append(callback)


class _ResolvedItemsView(ItemsView):
    def __iter__(self):
        for key in list(self._mapping):
            try:
                yield key, self._mapping[key]
            except KeyError:
                continue


class _ResolvedValuesView(ValuesView):
    def __iter__(self):
        for key in list(self._mapping):
            try:
                yield self._mapping[key]
            except KeyError:
                continue


class LazyTypeSet(MutableSet):
    """Set of registered program types, built from the registry on first read.

    Adding and discarding types does not trigger any imports. Reading the set
    (membership, iteration, length) imports every installed SDK once.
    """

    @classmethod
    def _from_iterable(cls, it: Iterable[Type[Any]]) -> set[Type[Any]]:
        # Set operators (|, &, -, ^) build their result through this hook.
        return set(it)

    def __init__(self, registry: LazyTypeRegistry):
        self._registry: Optional[LazyTypeRegistry] = registry
        self._items: set[Type[Any]] = set()
        self._discarded: set[Type[Any]] = set()
        self._lock = threading.RLock()

    def _materialize(self) -> set[Type[Any]]:
        if self._registry is not None:
            with self._lock:
                if self._registry is not None:
                    values = set(self._registry.values())
                    self._items = (self._items | values) - self._discarded
                    self._discarded.clear()
                    self._registry = None
        return self._items

    def __contains__(self, item: object) -> bool:
        return item in self._materialize()

    def __iter__(self) -> Iterator[Type[Any]]:
        return iter(set(self._materialize()))

    def __len__(self) -> int:
        return len(self._materialize())

    def __repr__(self) -> str:
        return repr(self._materialize())

    def add(self, value: Type[Any]) -> None:
        with self._lock:
            self._discarded.discard(value)
            self._items.add(value)

    def discard(self, value: Type[Any]) -> None:
        with self._lock:
            self._items.discard(value)
            if self._registry is not None:
                self._discarded.add(value)

    def copy(self) -> set[Type[Any]]:
        """Return the registered types as a plain set."""
        return set(self._materialize())

    __copy__ = copy

    def __deepcopy__(self, memo: dict) -> set[Type[Any]]:
        return set(self._materialize())

    def __reduce__(self):
        return (set, (list(self._materialize()),))

    def update(self, values: Iterable[Type[Any]]) -> None:
        """Add each of the given types."""
        for value in values:
            self.add(value)


def _available(lazy_types: dict[str, _LazyType]) -> dict[str, _LazyType]:
    return {alias: ref for alias, ref in lazy_types.items() if _module_available(ref.module)}


static_type_registry: dict[str, Type[Any]] = {
    metatype.__alias__: metatype.__bound__ for metatype in BOUND_QBRAID_META_TYPES
}
qbraid_meta_type_registry: dict[str, Type[Any]] = {
    metatype.__alias__: metatype for metatype in QBRAID_META_TYPES
}

NATIVE_REGISTRY: LazyTypeRegistry = LazyTypeRegistry(
    _available(_NATIVE_LAZY_TYPES) | static_type_registry | qbraid_meta_type_registry
)
_QPROGRAM_REGISTRY: LazyTypeRegistry = LazyTypeRegistry(
    NATIVE_REGISTRY._data | _available(_NON_NATIVE_LAZY_TYPES)
)
_QPROGRAM_ALIASES: set[str] = set(_QPROGRAM_REGISTRY.keys())
_QPROGRAM_TYPES: LazyTypeSet = LazyTypeSet(_QPROGRAM_REGISTRY)

_QPROGRAM_REGISTRY.on_drop(_QPROGRAM_ALIASES.discard)
