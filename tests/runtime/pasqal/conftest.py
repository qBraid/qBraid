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

"""Fixtures for Pasqal runtime tests."""

import importlib.machinery
import sys
import types

import pytest


@pytest.fixture(autouse=True)
def _pulser_stub(monkeypatch):
    """Install a minimal pulser stub scoped to each test.

    Uses monkeypatch so the stub is automatically removed after each test,
    preventing it from leaking into other test modules (e.g. azure tests).
    Only installs the stub when the real pulser package is not available.
    """
    existing = sys.modules.get("pulser")
    # Real pulser is loaded if it has AnalogDevice (our stub does not)
    if existing is not None and hasattr(existing, "AnalogDevice"):
        return  # real pulser available — nothing to do

    pulser = types.ModuleType("pulser")

    class Sequence:
        """Minimal Pulser Sequence stub."""

        def __init__(self, abstract_repr: str = '{"stub": true}'):
            self._abstract_repr = abstract_repr

        def to_abstract_repr(self) -> str:
            """Return the abstract representation string."""
            return self._abstract_repr

    pulser.Sequence = Sequence  # type: ignore[attr-defined]
    pulser.__spec__ = importlib.machinery.ModuleSpec("pulser", None)
    monkeypatch.setitem(sys.modules, "pulser", pulser)
