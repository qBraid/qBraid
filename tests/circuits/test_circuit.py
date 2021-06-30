# -*- coding: utf-8 -*-
# All rights reserved-2019©.
import numpy as np
import pytest


## SET BACKEND
import matplotlib as mpl
mpl.use("TkAgg")


import qbraid.circuits.update_rule
from qbraid.circuits.circuit import Circuit
from qbraid.circuits.moment import Moment
from qbraid.circuits.instruction import Instruction


def circuit():
    return Circuit(num_qubits=3,name="test_circuit")
   
@pytest.fixture()
def moment():
    return Moment()


"""
INSTRCUTIONS
"""

"""
MOMENTS
"""


"""
CIRCUITS
"""
@pytest.mark.parametrize('circuit_param, expected', [
        (circuit(), {'_qubits':[0,1,2],'_moments':[],'name':'test_circuit','update_rule': qbraid.circuits.update_rule.UpdateRule.NEW_THEN_INLINE}),])
def test_creating_circuit(circuit_param,expected):
    # check class parameters
    dict = circuit_param.__dict__
    check_qubit = []
    for qubit_obj in dict['_qubits']:
        check_qubit.append(qubit_obj._index)
    dict['_qubits'] = check_qubit
    assert dict == expected

@pytest.mark.parametrize('circuit_param, expected', [
        ('_moments'==[]),])
def test_add_moment(moment,circuit_param, expected):
    # check class parameters
    circuit_param.append(moment)
    assert circuit_param._moments == expected
