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
