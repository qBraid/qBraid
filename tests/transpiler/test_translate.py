# Copyright (C) 2025 qBraid
#
# This file is part of the qBraid-SDK
#
# The qBraid-SDK is free software released under the GNU General Public License v3
# or later. You can redistribute and/or modify it under the terms of the GPL v3.
# See the LICENSE file in the project root or <https://www.gnu.org/licenses/gpl-3.0.html>.
#
# THERE IS NO WARRANTY for the qBraid-SDK, as per Section 15 of the GPL v3.

"""
Unit tests for the chain_calls function in qbraid.transpiler.converter.

"""
from cirq import Circuit
from openqasm3.ast import Program

from qbraid.transpiler.converter import chain_calls, translate

from .cirq_utils import _equal


def test_chain_calls_addition():
    """Test that chain_calls can add a sequence of numbers."""

    def add(x, y):
        return x + y

    result = chain_calls(add, 0, 1, 2, 3, 4)
    assert result == 10


def test_chain_calls_multiplication():
    """Test that chain_calls can multiply a sequence of numbers."""

    def multiply(x, y):
        return x * y

    result = chain_calls(multiply, 1, 2, 3, 4)
    assert result == 24


def test_chain_calls_with_kwargs():
    """Test that chain_calls can handle keyword arguments."""

    def power(x, y, exponent=1):
        return x + (y**exponent)

    result = chain_calls(power, 0, 2, 3, exponent=2)
    assert result == 13


def test_chain_calls_empty_args():
    """Test that chain_calls can handle an empty sequence of arguments."""

    def add(x, y):
        return x + y

    result = chain_calls(add, 5)
    assert result == 5


def test_chain_calls_non_numeric():
    """Test that chain_calls can concatenate a sequence of strings."""

    def concatenate(x, y):
        return x + y

    result = chain_calls(concatenate, "Hello", " ", "World", "!")
    assert result == "Hello World!"


def test_translate():
    """Test that translate can chain multiple transpile calls on a program."""
    qasm = """
    OPENQASM 2.0;
    include "qelib1.inc";
    qreg q[2];
    creg c[2];
    h q[0];
    cx q[0], q[1];
    measure q -> c;
    """

    program = translate(qasm, "openqasm3")
    circuit_one = translate(program, "qasm2", "cirq")
    circuit_two = translate(program, "qasm3", "braket", "cirq")

    assert isinstance(program, Program)
    assert all(isinstance(circuit, Circuit) for circuit in (circuit_one, circuit_two))
    assert _equal(circuit_one, circuit_two)
