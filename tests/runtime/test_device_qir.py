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
Unit tests for QbraidDevice, QbraidJob, and QbraidGateModelResultBuilder
classes using the qbraid_qir_simulator

"""
from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from ._resources import MockDevice

if TYPE_CHECKING:
    import pyqir
    from pyqir import Module

pyqir = pytest.importorskip("pyqir")


@pytest.fixture
def pyqir_module() -> Module:
    """Returns a one-qubit PyQIR module with Hadamard gate and measurement."""
    bell = pyqir.SimpleModule("test_qir_program", num_qubits=1, num_results=1)
    qis = pyqir.BasicQisBuilder(bell.builder)

    qis.h(bell.qubits[0])
    qis.mz(bell.qubits[0], bell.results[0])

    return bell._module


def test_device_transform(pyqir_module: Module, mock_qbraid_device):
    """Test transform method on OpenQASM 2 string."""
    assert mock_qbraid_device.prepare(pyqir_module) == {"bitcode": pyqir_module.bitcode}


def test_transform_to_ir_from_spec(mock_basic_device: MockDevice, pyqir_module: Module):
    """Test transforming to run input to given IR from target profile program spec."""
    run_input_transformed = mock_basic_device.transform(pyqir_module)
    run_input_ir = mock_basic_device.prepare(run_input_transformed)
    assert isinstance(run_input_ir, dict)
    assert isinstance(run_input_ir.get("bitcode"), bytes)

    mock_basic_device._target_spec = None
    run_input_transformed = mock_basic_device.transform(pyqir_module)
    run_input_ir = mock_basic_device.prepare(run_input_transformed)
    assert isinstance(run_input_ir, pyqir.Module)
