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
Unit test for quantum program registry for QIR

"""
from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from qbraid.programs import ExperimentType, ProgramSpec, unregister_program_type

if TYPE_CHECKING:
    import pyqir
    from pyqir import Module

pyqir = pytest.importorskip("pyqir")


@pytest.fixture
def pyqir_bell() -> Module:
    """Returns a QIR bell circuit with measurement over two qubits."""
    bell = pyqir.SimpleModule("test_qir_bell", num_qubits=2, num_results=2)
    qis = pyqir.BasicQisBuilder(bell.builder)

    qis.h(bell.qubits[0])
    qis.cx(bell.qubits[0], bell.qubits[1])
    qis.mz(bell.qubits[0], bell.results[0])
    qis.mz(bell.qubits[1], bell.results[1])

    return bell._module


@pytest.fixture
def pyqir_spec() -> ProgramSpec:
    """Returns a ProgramSpec for the QIR bell circuit."""
    return ProgramSpec(pyqir.Module, alias="pyqir", serialize=lambda module: module.bitcode)


def test_load_program_pyqir(pyqir_bell: Module, pyqir_spec: ProgramSpec):
    """Test program spec to IR conversion for a QIR program."""
    program_ir = pyqir_spec.serialize(pyqir_bell)
    assert isinstance(program_ir, bytes)
    assert program_ir == pyqir_bell.bitcode


def test_program_spec_specify_experiment_type():
    """Test specifying the experiment type for a program spec."""
    try:
        spec = ProgramSpec(bytes, alias="llvm", experiment_type=ExperimentType.OTHER)
        assert spec.experiment_type == ExperimentType.OTHER
    finally:
        unregister_program_type("llvm", raise_error=False)
