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


@pytest.fixture
def cudaq_to_qasm2_with_stub():
    """Load the conversion module against a stubbed ``cudaq``, so its logic is
    testable even where the real cudaq package fails to import (as in CI)."""
    real_cudaq = sys.modules.get("cudaq")
    stub = types.ModuleType("cudaq")
    sys.modules["cudaq"] = stub
    if MODULE in sys.modules:
        module = importlib.reload(sys.modules[MODULE])
    else:
        module = importlib.import_module(MODULE)
    yield module, stub
    if real_cudaq is not None:
        sys.modules["cudaq"] = real_cudaq
        importlib.reload(sys.modules[MODULE])
    else:
        sys.modules.pop("cudaq", None)
        sys.modules.pop(MODULE, None)


def test_cudaq_to_qasm2_raises_on_failed_translation(cudaq_to_qasm2_with_stub):
    """cudaq.translate signals failure by returning '{translation failed}'; the
    conversion must raise instead of passing it along as valid QASM2."""
    module, stub = cudaq_to_qasm2_with_stub
    stub.translate = lambda *args, **kwargs: "{translation failed}"
    with pytest.raises(ProgramConversionError, match="failed to produce QASM2"):
        module.cudaq_to_qasm2(object())


def test_cudaq_to_qasm2_returns_valid_qasm(cudaq_to_qasm2_with_stub):
    """A successful translation passes through unchanged."""
    module, stub = cudaq_to_qasm2_with_stub
    stub.translate = lambda *args, **kwargs: 'OPENQASM 2.0;\ninclude "qelib1.inc";\n'
    assert module.cudaq_to_qasm2(object()).startswith("OPENQASM 2.0;")
