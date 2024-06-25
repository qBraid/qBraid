# Copyright (C) 2024 qBraid
#
# This file is part of the qBraid-SDK
#
# The qBraid-SDK is free software released under the GNU General Public License v3
# or later. You can redistribute and/or modify it under the terms of the GPL v3.
# See the LICENSE file in the project root or <https://www.gnu.org/licenses/gpl-3.0.html>.
#
# THERE IS NO WARRANTY for the qBraid-SDK, as per Section 15 of the GPL v3.

"""
Unit tests for interfacing quantum programs

"""
import pytest

from qbraid._version import __version__
from qbraid.interface import circuits_allclose, random_circuit
from qbraid.programs.exceptions import QbraidError
from qbraid.transpiler import transpile


@pytest.mark.parametrize("num_qubits, depth, max_operands, seed", [(1, 1, 1, 42)])
def test_qasm3_random(num_qubits, depth, max_operands, seed):
    """Test that _qasm3_random generates the correct QASM code."""
    expected_output = f"""
// Generated by qBraid v{__version__}
OPENQASM 3.0;
include "stdgates.inc";
/*
    seed = {seed}
    num_qubits = {num_qubits}
    depth = {depth}
    max_operands = {max_operands}
*/
qubit[1] q;
bit[1] c;
x q[0];
c[0] = measure q[0];
"""
    output = random_circuit(
        "qasm3",
        num_qubits=num_qubits,
        depth=depth,
        max_operands=max_operands,
        seed=seed,
        measure=True,
    )
    assert output == expected_output

def test_bad_qasm3_random():
    """Test that _qasm3_random raises a QbraidError when it fails."""
    with pytest.raises(QbraidError):
        random_circuit("qasm3", seed="12")

@pytest.mark.parametrize("param", ["num_qubits", "depth", "max_operands"])
def test_qasm3_zero_value_raises(param):
    """Test that _qasm3_random raises a ValueError when a circuit parameter is <=0."""
    params = {param: 0}
    expected_err = f"Invalid random circuit options. {param} must be a positive integer."
    with pytest.raises(ValueError, match=expected_err):
        random_circuit("qasm3", **params)


@pytest.mark.parametrize("package", ["qiskit", "cirq"])
def test_random_circuit_raises_for_bad_params(package: str):
    """Test that _cirq_random raises a QbraidError for invalid parameters."""
    expected_err = f"Failed to create {package.capitalize()} random circuit"
    with pytest.raises(QbraidError, match=expected_err):
        random_circuit(package, num_qubits=-1)

def test_circuits_allclose():
    """Test circuit allclose function."""
    circuit0 = random_circuit("pytket", num_qubits=2, depth=2)
    circuit1 = transpile(circuit0, "braket")
    assert circuits_allclose(circuit1, circuit0, index_contig = True, allow_rev_qubits=True)

    circuit2 = random_circuit("qiskit", num_qubits=3, depth=2)
    assert not circuits_allclose(circuit2, circuit0, index_contig = True, allow_rev_qubits=True)
