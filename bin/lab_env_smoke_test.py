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
Smoke test for a qBraid-SDK Lab environment. Run it with the environment's own Python.

Usage:
    <env>/pyenv/bin/python bin/lab_env_smoke_test.py VERSION

"""

import platform
import sys

# Lab needs ipykernel to start the kernel. The rest come from the installed extras.
# pylint: disable=unused-import
import ipykernel  # noqa: F401
import matplotlib
import pennylane  # noqa: F401

import qbraid
from qbraid import transpile
from qbraid.visualization import circuit_drawer

# pylint: enable=unused-import

PROGRAM = """
OPENQASM 3.0;
include "stdgates.inc";
qubit[2] q;
h q[0];
cx q[0], q[1];
"""

# Transpiler targets from the installed extras: qiskit, cirq, braket, pytket and qir.
TARGETS = ["qiskit", "cirq", "braket", "pytket", "pyqir"]


def main() -> None:
    """Check the qbraid version, then transpile a Bell circuit to each installed framework."""
    expected = sys.argv[1]
    if qbraid.__version__ != expected:
        sys.exit(f"qbraid {qbraid.__version__} installed, expected {expected}")

    for target in TARGETS:
        program = transpile(PROGRAM, target)
        print(f"{target}: {type(program).__module__}.{type(program).__name__}")

    # The visualization extra: draw the circuit without a display.
    matplotlib.use("Agg")
    circuit_drawer(transpile(PROGRAM, "qiskit"), output="mpl")
    print(f"qbraid {qbraid.__version__}, Python {platform.python_version()}, {platform.machine()}")


if __name__ == "__main__":
    main()
