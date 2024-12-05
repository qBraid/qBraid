
"""
Unit test for quantum program registry for QIR

"""
import random
import string
import sys
import unittest.mock

import pytest
 
from qbraid.exceptions import QbraidError
from qbraid.interface import random_circuit
from qbraid.programs import (
    QPROGRAM_ALIASES,
    QPROGRAM_REGISTRY,
    QPROGRAM_TYPES,
    ExperimentType,
    ProgramSpec,
    derive_program_type_alias,
    get_program_type_alias,
    load_program,
    register_program_type,
    unregister_program_type,
)
from qbraid.programs.exceptions import ProgramTypeError
from qbraid.programs.registry import get_native_experiment_type, is_registered_alias_native
from qbraid.programs.typer import IonQDict

pyqir = pytest.importorskip('pyqir')
from pyqir import BasicQisBuilder, Module, SimpleModule

@pytest.fixture
def pyqir_bell() -> Module:
    """Returns a QIR bell circuit with measurement over two qubits."""
    bell = SimpleModule("test_qir_bell", num_qubits=2, num_results=2)
    qis = BasicQisBuilder(bell.builder)

    qis.h(bell.qubits[0])
    qis.cx(bell.qubits[0], bell.qubits[1])
    qis.mz(bell.qubits[0], bell.results[0])
    qis.mz(bell.qubits[1], bell.results[1])

    return bell._module

@pytest.fixture
def pyqir_spec() -> ProgramSpec:
    """Returns a ProgramSpec for the QIR bell circuit."""
    return ProgramSpec(Module, alias="pyqir", to_ir=lambda module: module.bitcode)

def test_load_program_pyqir(pyqir_bell: Module, pyqir_spec: ProgramSpec):
    """Test program spec to IR conversion for a QIR program."""
    program_ir = pyqir_spec.to_ir(pyqir_bell)
    assert isinstance(program_ir, bytes)
    assert program_ir == pyqir_bell.bitcode

def test_program_spec_specify_experiment_type():
    """Test specifying the experiment type for a program spec."""
    try:
        spec = ProgramSpec(bytes, alias="llvm", experiment_type=ExperimentType.OTHER)
        assert spec.experiment_type == ExperimentType.OTHER
    finally:
        unregister_program_type("llvm", raise_error=False)