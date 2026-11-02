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

"""Fresh-process checks for optional conversion dependencies."""

import subprocess
import sys

import pytest


@pytest.mark.parametrize("missing", [("pytket",), ("pytket", "cirq"), ("pytket", "cirq", "qiskit")])
def test_qasm2_conversion_without_optional_sdks(missing):
    """A fresh registry keeps base QASM conversions when optional SDKs are absent."""
    script = r"""
import sys
for name in sys.argv[1:]:
    sys.modules[name] = None

from qbraid import transpile
from qbraid.transpiler.conversions import conversion_functions
import openqasm3
from openqasm3.ast import QuantumGate

# Check the first registration: a retry can hide a failed package import.
assert "qasm2_to_qasm3" in conversion_functions, conversion_functions
assert "qasm2_to_ionq" in conversion_functions, conversion_functions
assert "qasm2_to_pytket" not in conversion_functions, conversion_functions
if "qiskit" not in sys.argv[1:]:
    assert "qasm2_to_qiskit" in conversion_functions, conversion_functions
source = 'OPENQASM 2.0; include "qelib1.inc"; qreg q[1]; h q[0];'
output = transpile(source, "qasm3")
program = openqasm3.parse(output)
assert program.version == "3.0", output
assert [stmt.name.name for stmt in program.statements if isinstance(stmt, QuantumGate)] == ["h"]
"""
    result = subprocess.run(
        [sys.executable, "-c", script, *missing],
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
