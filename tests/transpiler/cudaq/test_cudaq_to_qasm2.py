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
Unit tests for the CUDA-Q to QASM2 conversion.

"""
import importlib
import sys
import types

import pytest

from qbraid.transpiler.exceptions import ProgramConversionError

MODULE = "qbraid.transpiler.conversions.cudaq.cudaq_to_qasm2"


class _StubKernel:
    """Minimal stand-in for a PyKernel: the conversion compiles before translating."""

    def compile(self):
        """No-op; the stubbed cudaq.translate is what the test drives."""


PARENT, _, ATTR = MODULE.rpartition(".")


@pytest.fixture
def cudaq_to_qasm2_with_stub():
    """Load the conversion module against a stubbed ``cudaq``, so its logic is
    testable even where the real cudaq package fails to import (as in CI).

    Everything mutated is restored in ``finally``. Reloading rebinds the module on its
    parent package too, so leaving that behind would hand a later import the stub-backed
    module -- and a failure during setup would leave the stub installed for everyone.
    """
    sentinel = object()
    real_cudaq = sys.modules.get("cudaq", sentinel)
    real_module = sys.modules.get(MODULE, sentinel)
    parent = sys.modules.get(PARENT)
    real_attr = getattr(parent, ATTR, sentinel) if parent is not None else sentinel

    stub = types.ModuleType("cudaq")
    sys.modules["cudaq"] = stub
    try:
        if MODULE in sys.modules:
            module = importlib.reload(sys.modules[MODULE])
        else:
            module = importlib.import_module(MODULE)
        yield module, stub
    finally:
        for name, saved in (("cudaq", real_cudaq), (MODULE, real_module)):
            if saved is sentinel:
                sys.modules.pop(name, None)
            else:
                sys.modules[name] = saved
        # Reload against the real cudaq so the cached module is not stub-backed.
        if real_module is not sentinel and real_cudaq is not sentinel:
            importlib.reload(sys.modules[MODULE])
        if parent is not None:
            if real_attr is sentinel:
                delattr(parent, ATTR) if hasattr(parent, ATTR) else None
            else:
                setattr(parent, ATTR, real_attr)


def test_cudaq_to_qasm2_raises_on_failed_translation(cudaq_to_qasm2_with_stub):
    """cudaq.translate signals failure by returning '{translation failed}'; the
    conversion must raise instead of passing it along as valid QASM2."""
    module, stub = cudaq_to_qasm2_with_stub
    stub.translate = lambda *args, **kwargs: "{translation failed}"
    with pytest.raises(ProgramConversionError, match="failed to produce QASM2"):
        module.cudaq_to_qasm2(_StubKernel())


def test_cudaq_to_qasm2_returns_valid_qasm(cudaq_to_qasm2_with_stub):
    """A successful translation passes through unchanged."""
    module, stub = cudaq_to_qasm2_with_stub
    qasm = 'OPENQASM 2.0;\ninclude "qelib1.inc";\n'
    stub.translate = lambda *args, **kwargs: qasm
    # Full equality, not startswith: the point is that a successful translation is
    # returned untouched, which a header-only check would not catch.
    assert module.cudaq_to_qasm2(_StubKernel()) == qasm
