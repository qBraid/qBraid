# Copyright 2026 qBraid
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
Tests that the generated Pauli-operator conversions are complete and current.

Everything here reads source with ``ast`` rather than importing, so the checks hold on a
machine with none of the operator libraries installed -- which is exactly the machine on
which a missing edge would otherwise go unnoticed.

"""
from __future__ import annotations

import ast
import importlib.util
import itertools
import pathlib

import pytest

REPO = pathlib.Path(__file__).parents[3]
SCRIPT = REPO / "bin" / "generate_operator_conversions.py"
CONVERSIONS = REPO / "qbraid" / "transpiler" / "conversions"


@pytest.fixture(scope="module")
def codegen():
    """Load the generator script as a module."""
    spec = importlib.util.spec_from_file_location("generate_operator_conversions", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _functions(path: pathlib.Path) -> set[str]:
    """Module-level function names defined in one file."""
    return {
        node.name
        for node in ast.parse(path.read_text()).body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }


def _operator_types() -> set[str]:
    """Keys of ``OPERATOR_TYPES`` in ``qbraid/programs/_import.py``."""
    for node in ast.parse((REPO / "qbraid" / "programs" / "_import.py").read_text()).body:
        target = getattr(node, "target", None) or (getattr(node, "targets", None) or [None])[0]
        if getattr(target, "id", None) == "OPERATOR_TYPES" and isinstance(node.value, ast.Dict):
            return {key.value for key in node.value.keys}
    raise AssertionError("OPERATOR_TYPES not found in qbraid/programs/_import.py")


def test_generated_packages_are_current(codegen):
    """The committed packages are exactly what the generator writes."""
    stale = [
        str(path.relative_to(REPO))
        for path, text in codegen.render().items()
        if not path.exists() or path.read_text() != text
    ]
    assert not stale, f"{stale} are stale -- run `python bin/generate_operator_conversions.py`"


def test_every_library_has_a_reader_and_a_writer(codegen):
    """Each generated one-liner calls read_<source> and write_<target>; both must exist."""
    helpers = _functions(CONVERSIONS / "_pauli_io.py")
    libraries = set(codegen.LIBRARIES)
    assert {name[len("read_") :] for name in helpers if name.startswith("read_")} == libraries
    assert {name[len("write_") :] for name in helpers if name.startswith("write_")} == libraries


def test_every_library_is_a_registered_operator_type(codegen):
    """A library whose type is not registered would get edges transpile() can never use."""
    assert set(codegen.LIBRARIES) <= _operator_types()


def test_every_ordered_pair_is_declared(codegen):
    """Each library converts directly to every other one."""
    declared = set()
    for source in codegen.LIBRARIES:
        declared |= _functions(CONVERSIONS / source / f"{source}_extras.py")
    missing = {
        f"{source}_to_{target}"
        for source, target in itertools.permutations(codegen.LIBRARIES, 2)
        if f"{source}_to_{target}" not in declared
    }
    assert not missing


def test_every_feeder_converts_into_a_canonical_library(codegen):
    """A registered operator type that is not canonical must have a hand-written edge into
    one, or it is recognized by transpile() but reaches nothing."""
    feeders = _operator_types() - set(codegen.LIBRARIES)
    assert feeders, "expected feeder aliases (e.g. cirq_pauli_string)"
    for feeder in feeders:
        functions = set().union(*(_functions(path) for path in (CONVERSIONS / feeder).glob("*.py")))
        assert any(
            f"{feeder}_to_{library}" in functions for library in codegen.LIBRARIES
        ), f"feeder '{feeder}' has no conversion into a canonical operator library"
