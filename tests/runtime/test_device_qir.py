# Copyright (C) 2024 qBraid
#
# This file is part of the qBraid-SDK
#
# The qBraid-SDK is free software released under the GNU General Public License v3
# or later. You can redistribute and/or modify it under the terms of the GPL v3.
# See the LICENSE file in the project root or <https://www.gnu.org/licenses/gpl-3.0.html>.
#
# THERE IS NO WARRANTY for the qBraid-SDK, as per Section 15 of the GPL v3.

# pylint: disable=redefined-outer-name,unused-argument,too-many-lines

"""
Unit tests for QbraidDevice, QbraidJob, and QbraidGateModelResultBuilder
classes using the qbraid_qir_simulator

"""
import importlib.util
import json
import logging
import time
from typing import Any
from unittest.mock import Mock, PropertyMock, patch

import cirq
import numpy as np
import pytest
from pandas import DataFrame


from qbraid_core.services.quantum.exceptions import QuantumServiceRequestError

from qbraid._caching import cache_disabled
from qbraid.programs import (
    ExperimentType,
    ProgramSpec,
    register_program_type,
    unregister_program_type,
)
from qbraid.programs.exceptions import ProgramTypeError
from qbraid.programs.typer import IonQDict, QuboCoefficientsDict
from qbraid.runtime import DeviceStatus, JobStatus, ProgramValidationError, Result, TargetProfile
from qbraid.runtime.exceptions import QbraidRuntimeError, ResourceNotFoundError
from qbraid.runtime.native import QbraidDevice, QbraidJob, QbraidProvider
from qbraid.runtime.native.provider import get_program_spec_lambdas
from qbraid.runtime.native.result import (
    NECVectorAnnealerResultData,
    QbraidQirSimulatorResultData,
    QuEraQasmSimulatorResultData,
)
from qbraid.runtime.noise import NoiseModel, NoiseModelSet
from qbraid.runtime.options import RuntimeOptions
from qbraid.runtime.schemas.experiment import QuboSolveParams
from qbraid.runtime.schemas.job import RuntimeJobModel
from qbraid.transpiler import Conversion, ConversionGraph, ConversionScheme, ProgramConversionError

from ._resources import (
    DEVICE_DATA_QIR,
    JOB_DATA_NEC,
    JOB_DATA_QIR,
    JOB_DATA_QUERA_QASM,
    RESULTS_DATA_NEC,
    RESULTS_DATA_QUERA_QASM,
    MockDevice,
)

pytest.importorskip('pyqir')
from pyqir import Module, SimpleModule, BasicQisBuilder

@pytest.fixture
def pyqir_module() -> Module:
    """Returns a one-qubit PyQIR module with Hadamard gate and measurement."""
    bell = SimpleModule("test_qir_program", num_qubits=1, num_results=1)
    qis = BasicQisBuilder(bell.builder)

    qis.h(bell.qubits[0])
    qis.mz(bell.qubits[0], bell.results[0])

    return bell._module


def test_device_transform(pyqir_module, mock_qbraid_device):
    """Test transform method on OpenQASM 2 string."""
    assert mock_qbraid_device.to_ir(pyqir_module) == {"bitcode": pyqir_module.bitcode}

    
def test_transform_to_ir_from_spec(mock_basic_device: MockDevice, pyqir_module: Module):
    """Test transforming to run input to given IR from target profile program spec."""
    run_input_transformed = mock_basic_device.transform(pyqir_module)
    run_input_ir = mock_basic_device.to_ir(run_input_transformed)
    assert isinstance(run_input_ir, dict)
    assert isinstance(run_input_ir.get("bitcode"), bytes)

    mock_basic_device._target_spec = None
    run_input_transformed = mock_basic_device.transform(pyqir_module)
    run_input_ir = mock_basic_device.to_ir(run_input_transformed)
    assert isinstance(run_input_ir, Module)