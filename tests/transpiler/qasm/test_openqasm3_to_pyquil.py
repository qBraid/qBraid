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
Unit tests for OpenQASM 3 AST to pyQuil Program conversion.

"""
import openqasm3
import pytest

from qbraid.transpiler import ConversionGraph
from qbraid.transpiler.conversions.openqasm3 import openqasm3_to_pyquil

pyquil = pytest.importorskip("pyquil")


def test_openqasm3_to_pyquil_bell_program():
    """Test converting an OpenQASM 3 AST program to a pyQuil Program."""
    program = openqasm3.parse(
        """
        OPENQASM 3.0;
        include "stdgates.inc";

        qubit[2] q;

        h q[0];
        cx q[0], q[1];
        """
    )

    quil_program = openqasm3_to_pyquil(program)

    assert isinstance(quil_program, pyquil.Program)
    assert quil_program.out() == "H 0\nCNOT 0 1\n"


def test_openqasm3_to_pyquil_parameters_and_measurements():
    """Test converting parameterized gates and measurements to a pyQuil Program."""
    program = openqasm3.parse(
        """
        OPENQASM 3.0;
        include "stdgates.inc";

        qubit[2] q;
        bit[2] c;

        rx(pi / 2) q[0];
        sdg q[0];
        t q[1];
        measure q[0] -> c[0];
        measure q[1] -> c[1];
        """
    )

    quil_program = openqasm3_to_pyquil(program)

    assert quil_program.out() == (
        "DECLARE c BIT[2]\n"
        "RX(1.5707963267948966) 0\n"
        "PHASE(-1.5707963267948966) 0\n"
        "T 1\n"
        "MEASURE 0 c[0]\n"
        "MEASURE 1 c[1]\n"
    )


def test_conversion_graph_has_direct_openqasm3_to_pyquil_edge():
    """Test that OpenQASM 3 AST to pyQuil is registered as a direct conversion."""
    graph = ConversionGraph(nodes={"openqasm3", "pyquil"}, include_isolated=True)

    assert graph.has_edge("openqasm3", "pyquil")
