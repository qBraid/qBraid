# -*- coding: utf-8 -*-
# All rights reserved-2019©.
import numpy as np
import pytest

import qiskit
qiskit.QuantumCircuit
## SET BACKEND
import matplotlib as mpl
mpl.use("TkAgg")

import qiskit

qiskit.QuantumCircuit()

import qbraid.circuits.update_rule
from qbraid.circuits.circuit import Circuit
from qbraid.circuits.moment import Moment
from qbraid.circuits.instruction import Instruction
import qbraid.circuits.library.standard_gates.dcx as dcx

#ideal from qbraid.circuits.standard_gates  import h, dcx


def get_qubit_idx_dict(dict:dict = None)->None:
    # get index of qubits
    check_qubit = []
    for qubit_obj in dict['_qubits']:
        check_qubit.append(qubit_obj._index)
    dict['_qubits'] = check_qubit

def circuit():
    return Circuit(num_qubits=3,name="test_circuit")
   

@pytest.fixture()
def instruction(gate):
    return Instruction(gate = gate)

@pytest.fixture()
def moment(instruction):
    return Moment(instructions=instruction)


"""
INSTRCUTIONS
"""

"""
MOMENTS
"""
""" @pytest.mark.parametrize('circuit_param, expected', [
        (circuit(),'_moments'==[]),])
def test_moment_w_instruction(moment,circuit_param, expected):
    # check class parameter
    circuit_param.append(moment)
    assert circuit_param._moments == expected """

"""
CIRCUITS
"""
@pytest.mark.parametrize('circuit_param, expected', [
        (circuit(), {'_qubits':[0,1,2],'_moments':[],'name':'test_circuit','update_rule': qbraid.circuits.update_rule.UpdateRule.NEW_THEN_INLINE}),])
def test_creating_circuit(circuit_param,expected):
    # check class parameters
    dict = circuit_param.__dict__
    get_qubit_idx_dict(dict)
    assert dict == expected

@pytest.mark.parametrize('circuit_param, expected', [
        (circuit(), {'_qubits':[0,1,2],'_moments':[],'name':'test_circuit','update_rule': qbraid.circuits.update_rule.UpdateRule.NEW_THEN_INLINE}),])
def test_add_moment(moment,circuit_param, expected):
    # check class parameter
    circuit_param.append(moment)
    dict = circuit_param.__dict__
    get_qubit_idx_dict(dict)
    assert dict == expected

