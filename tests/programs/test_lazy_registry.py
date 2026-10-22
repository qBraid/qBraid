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
Unit tests for the lazy program type registry, and a guard that importing
qbraid.programs does not import optional quantum SDKs.

"""
import copy
import importlib
import json
import logging
import os
import pickle
import subprocess
import sys
import types
import typing

import pytest

import qbraid.programs
from qbraid.programs._import import (
    _NATIVE_LAZY_TYPES,
    _NON_NATIVE_LAZY_TYPES,
    LazyTypeRegistry,
    LazyTypeSet,
    _LazyType,
    _module_available,
)
from qbraid.programs.registry import QPROGRAM_ALIASES, QPROGRAM_REGISTRY, unregister_program_type

# openqasm3 is a core dependency that qbraid.programs imports directly.
OPTIONAL_SDK_ROOTS = sorted(
    {ref.module.split(".")[0] for ref in (_NATIVE_LAZY_TYPES | _NON_NATIVE_LAZY_TYPES).values()}
    - {"openqasm3"}
)

INSTALLED_ALIASES = sorted(
    alias
    for alias, ref in (_NATIVE_LAZY_TYPES | _NON_NATIVE_LAZY_TYPES).items()
    if alias != "openqasm3" and _module_available(ref.module)
)


def _imported_sdks_after(code: str) -> list[str]:
    """Run code in a fresh interpreter and return the optional SDKs it imported."""
    script = (
        "import json, sys\n"
        f"{code}\n"
        f"print(json.dumps(sorted(m for m in {OPTIONAL_SDK_ROOTS!r} if m in sys.modules)))\n"
    )
    result = subprocess.run(
        [sys.executable, "-c", script], capture_output=True, text=True, check=True
    )
    return json.loads(result.stdout.strip().splitlines()[-1])


@pytest.mark.parametrize(
    "code",
    [
        "import qbraid.programs",
        "from qbraid.programs import QPROGRAM_ALIASES, QPROGRAM_REGISTRY, NATIVE_REGISTRY",
        "from qbraid.programs import get_program_type_alias\n"
        "get_program_type_alias('OPENQASM 3.0;\\nqubit[1] q;\\nh q[0];')",
        "from qbraid.programs import load_program\n"
        "load_program('OPENQASM 2.0;\\ninclude \"qelib1.inc\";\\nqreg q[1];\\nh q[0];')",
        "from qbraid.programs import get_program_type_alias\n"
        "get_program_type_alias({'not': 'a program'}, safe=True)",
    ],
)
def test_qbraid_programs_does_not_import_optional_sdks(code):
    """Importing and using qbraid.programs on non-SDK input must not import any SDK."""
    assert _imported_sdks_after(code) == []


@pytest.mark.skipif(not INSTALLED_ALIASES, reason="No optional SDKs installed")
def test_installed_sdk_aliases_listed_without_import():
    """Installed SDKs are listed as aliases before anything imports them."""
    code = (
        "from qbraid.programs import QPROGRAM_ALIASES\n"
        f"missing = sorted(set({INSTALLED_ALIASES!r}) - QPROGRAM_ALIASES)\n"
        "assert not missing, missing"
    )
    assert _imported_sdks_after(code) == []


def test_lookup_resolves_installed_type():
    """Looking up an installed alias returns the SDK's program type."""
    if "cirq" not in QPROGRAM_ALIASES:
        pytest.skip("cirq not installed")

    import cirq  # pylint: disable=import-outside-toplevel

    assert QPROGRAM_REGISTRY["cirq"] is cirq.Circuit
    assert QPROGRAM_REGISTRY.is_loaded("cirq")


def test_qprogram_native_still_available():
    """QPROGRAM_NATIVE is still exposed, now built on access."""
    native = qbraid.programs.QPROGRAM_NATIVE
    assert str in typing.get_args(native)


@pytest.fixture
def probe_packages(tmp_path, monkeypatch):
    """Create an importable package and a package that fails to import."""
    good = tmp_path / "qbraid_probe_good"
    (good / "sub").mkdir(parents=True)
    (good / "__init__.py").write_text("class Program:\n    pass\n")
    (good / "sub" / "__init__.py").write_text("")
    bad = tmp_path / "qbraid_probe_bad"
    bad.mkdir()
    (bad / "__init__.py").write_text("raise ImportError('broken install')\n")
    monkeypatch.syspath_prepend(str(tmp_path))
    yield
    for name in list(sys.modules):
        if name.startswith(("qbraid_probe_good", "qbraid_probe_bad")):
            del sys.modules[name]


@pytest.mark.usefixtures("probe_packages")
def test_module_available_does_not_import():
    """Availability checks never import the module or its parents."""
    assert _module_available("qbraid_probe_good")
    assert _module_available("qbraid_probe_good.sub")
    assert not _module_available("qbraid_probe_good.missing")
    assert not _module_available("qbraid_probe_missing")
    assert not _module_available("qbraid_probe_missing.sub")
    assert "qbraid_probe_good" not in sys.modules


@pytest.mark.usefixtures("probe_packages")
def test_registry_resolves_on_lookup():
    """Membership and key iteration are import-free; lookup imports the type."""
    registry = LazyTypeRegistry({"probe": _LazyType("qbraid_probe_good", "Program"), "str": str})

    assert "probe" in registry
    assert list(registry) == ["probe", "str"]
    assert len(registry) == 2
    assert not registry.is_loaded("probe")
    assert dict(registry.loaded_items()) == {"str": str}
    assert "qbraid_probe_good" not in sys.modules

    program_type = registry["probe"]

    assert program_type is sys.modules["qbraid_probe_good"].Program
    assert registry.is_loaded("probe")
    assert dict(registry.loaded_items()) == {"probe": program_type, "str": str}


@pytest.mark.usefixtures("probe_packages")
def test_loaded_items_includes_types_imported_elsewhere():
    """An entry whose module was imported by the caller counts as loaded."""
    registry = LazyTypeRegistry({"probe": _LazyType("qbraid_probe_good", "Program")})

    import qbraid_probe_good  # pylint: disable=import-outside-toplevel,import-error

    assert dict(registry.loaded_items()) == {"probe": qbraid_probe_good.Program}


@pytest.mark.usefixtures("probe_packages")
def test_registry_drops_alias_that_fails_to_load(caplog):
    """A broken SDK install is dropped with a warning instead of silently."""
    registry = LazyTypeRegistry({"bad": _LazyType("qbraid_probe_bad", "Program"), "str": str})
    dropped = []
    registry.on_drop(dropped.append)

    with caplog.at_level(logging.WARNING):
        assert registry.get("bad") is None

    assert "bad" not in registry
    assert dropped == ["bad"]
    assert "Dropping program type alias 'bad'" in caplog.text
    assert dict(registry.items()) == {"str": str}


@pytest.mark.usefixtures("probe_packages")
def test_items_and_values_skip_broken_entries():
    """Full iteration resolves every entry and skips those that fail to load."""
    registry = LazyTypeRegistry(
        {
            "bad": _LazyType("qbraid_probe_bad", "Program"),
            "probe": _LazyType("qbraid_probe_good", "Program"),
        }
    )

    values = list(registry.values())

    assert values == [sys.modules["qbraid_probe_good"].Program]
    assert list(registry) == ["probe"]


@pytest.mark.usefixtures("probe_packages")
def test_copy_update_and_clear_keep_entries_lazy():
    """Backing up and restoring a registry does not import anything."""
    registry = LazyTypeRegistry({"probe": _LazyType("qbraid_probe_good", "Program")})

    backup = registry.copy()
    registry.clear()
    assert len(registry) == 0
    registry.update(backup)

    assert "probe" in registry
    assert not registry.is_loaded("probe")
    assert "qbraid_probe_good" not in sys.modules


@pytest.mark.usefixtures("probe_packages")
def test_type_set_defers_materialization():
    """Adding and discarding types does not import; reading builds the full set."""
    registry = LazyTypeRegistry({"probe": _LazyType("qbraid_probe_good", "Program"), "str": str})
    types = LazyTypeSet(registry)

    types.add(dict)
    types.discard(str)
    assert "qbraid_probe_good" not in sys.modules

    assert set(types) == {dict, sys.modules["qbraid_probe_good"].Program}
    types.discard(dict)
    assert dict not in types


def test_module_available_without_spec(monkeypatch):
    """A module in sys.modules without a spec cannot be searched for submodules."""
    monkeypatch.setitem(sys.modules, "qbraid_probe_nospec", types.ModuleType("qbraid_probe_nospec"))

    assert not _module_available("qbraid_probe_nospec.sub")


@pytest.mark.usefixtures("probe_packages")
def test_loaded_items_skips_missing_attribute():
    """An imported module that lacks the registered class is skipped, not raised."""
    registry = LazyTypeRegistry({"missing": _LazyType("qbraid_probe_good", "Missing")})

    importlib.import_module("qbraid_probe_good")

    assert not list(registry.loaded_items())
    assert "missing" not in registry


@pytest.mark.usefixtures("probe_packages")
def test_items_skip_broken_entries():
    """Iterating items resolves every entry and skips those that fail to load."""
    registry = LazyTypeRegistry({"bad": _LazyType("qbraid_probe_bad", "Program"), "str": str})

    assert dict(registry.items()) == {"str": str}


def test_type_set_copy_and_update():
    """copy returns a plain set and update adds each type."""
    types_set = LazyTypeSet(LazyTypeRegistry({"str": str}))
    types_set.update([dict, list])

    copied = types_set.copy()

    assert copied == {str, dict, list}
    assert isinstance(copied, set)


@pytest.mark.usefixtures("probe_packages")
def test_unregister_unloaded_alias_does_not_import():
    """Unregistering an alias that was never loaded removes it without importing."""
    alias = "qbraid_probe_lazy_alias"
    QPROGRAM_REGISTRY[alias] = _LazyType("qbraid_probe_good", "Program")
    QPROGRAM_ALIASES.add(alias)

    unregister_program_type(alias)

    assert alias not in QPROGRAM_REGISTRY
    assert alias not in QPROGRAM_ALIASES
    assert "qbraid_probe_good" not in sys.modules


def test_broken_sdk_does_not_break_transpiler(tmp_path):
    """An SDK found on disk that fails to import is skipped, not fatal.

    Shadows pytket with a package whose import raises, so its alias is listed but
    its conversion and wrapper modules cannot load.
    """
    (tmp_path / "pytket").mkdir()
    (tmp_path / "pytket" / "__init__.py").write_text("raise ImportError('broken install')\n")
    script = (
        "import qbraid.programs.gate_model as gate_model\n"
        "from qbraid.programs import QPROGRAM_ALIASES\n"
        "from qbraid.transpiler import ConversionGraph, transpile\n"
        "assert 'pytket' in QPROGRAM_ALIASES\n"
        "qasm2 = 'OPENQASM 2.0;\\ninclude \"qelib1.inc\";\\nqreg q[1];\\nh q[0];'\n"
        "out = transpile(qasm2, 'qasm3', conversion_graph=ConversionGraph())\n"
        "assert out.startswith('OPENQASM 3'), out\n"
        "assert not hasattr(gate_model, 'pytket')\n"
        "assert 'pytket' not in gate_model.__all__\n"
        "exec('from qbraid.programs.gate_model import *', {})\n"
    )
    env = {**os.environ, "PYTHONPATH": os.pathsep.join([str(tmp_path), *sys.path])}
    result = subprocess.run(
        [sys.executable, "-c", script], capture_output=True, text=True, env=env, check=False
    )

    assert result.returncode == 0, result.stderr
    assert "Skipping conversions for 'pytket'" in result.stderr


@pytest.mark.usefixtures("probe_packages")
def test_registry_supports_dict_operations():
    """Copying, pickling and merging keep working and keep entries unresolved."""
    registry = LazyTypeRegistry({"probe": _LazyType("qbraid_probe_good", "Program"), "str": str})

    for clone in (
        copy.copy(registry),
        copy.deepcopy(registry),
        pickle.loads(pickle.dumps(registry)),
        registry | {},
        {} | registry,
    ):
        assert isinstance(clone, LazyTypeRegistry)
        assert set(clone) == {"probe", "str"}
        assert not clone.is_loaded("probe")

    assert (registry | {"int": int})["int"] is int
    assert ({"str": int} | registry)["str"] is str
    registry |= {"int": int}
    assert registry["int"] is int
    assert "qbraid_probe_good" not in sys.modules


def test_type_set_supports_set_operations():
    """Set operators, copies and pickling return plain sets."""
    types_set = LazyTypeSet(LazyTypeRegistry({"str": str, "int": int}))

    assert types_set | {dict} == {str, int, dict}
    assert {dict} | types_set == {str, int, dict}
    assert types_set & {str} == {str}
    assert types_set - {str} == {int}
    assert types_set ^ {str, dict} == {int, dict}
    assert copy.deepcopy(types_set) == {str, int}
    assert pickle.loads(pickle.dumps(types_set)) == {str, int}
