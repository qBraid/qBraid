# Copyright (C) 2023 qBraid
#
# This file is part of the qBraid-SDK
#
# The qBraid-SDK is free software released under the GNU General Public License v3
# or later. You can redistribute and/or modify it under the terms of the GPL v3.
# See the LICENSE file in the project root or <https://www.gnu.org/licenses/gpl-3.0.html>.
#
# THERE IS NO WARRANTY for the qBraid-SDK, as per Section 15 of the GPL v3.

"""
Unit tests for defining custom conversions

"""
from unittest.mock import Mock

import cirq
import pytest

from qbraid.exceptions import PackageValueError
from qbraid.interface.random import random_circuit
from qbraid.transpiler.conversions.braket import braket_to_cirq
from qbraid.transpiler.edge import Conversion


def test_raise_for_unsupported_program_input():
    """Test that an exception is raised for an unsupported program input."""
    conversion = Conversion("braket", "cirq", braket_to_cirq)
    circuit = Mock()
    with pytest.raises(PackageValueError):
        conversion.convert(circuit)


def test_raise_for_source_program_input_mismatch():
    """Test that an exception is raised for a mismatch between the source package and input."""
    source, target, other = "braket", "cirq", "qiskit"
    conversion = Conversion(source, target, braket_to_cirq)
    circuit = random_circuit(other)
    with pytest.raises(ValueError):
        conversion.convert(circuit)


def test_braket_cirq_custom_conversion():
    """Test that a Braket to Cirq conversion is successful."""
    source, target = "braket", "cirq"
    conversion = Conversion(source, target, braket_to_cirq)
    braket_circuit = random_circuit(source)
    cirq_circuit = conversion.convert(braket_circuit)
    assert isinstance(cirq_circuit, cirq.Circuit)


def test_conversion_repr():
    """Test that the conversion repr is correct."""
    source, target = "braket", "cirq"
    conversion = Conversion(source, target, braket_to_cirq)
    assert repr(conversion) == f"('{source}', '{target}')"
