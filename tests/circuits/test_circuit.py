# -*- coding: utf-8 -*-
# All rights reserved-2019©.
import numpy as np
import pytest


import qiskit
qiskit.qiskit.circuit.measure.CircuitError

## SET BACKEND
import matplotlib as mpl
mpl.use("TkAgg")


from qbraid.circuits.circuit import Circuit
from qbraid.circuits.moment import Moment
from qbraid.circuits.instruction import Instruction


def circuit():
    return Circuit(num_qubits=3,name="test_circuit")
    

@pytest.mark.parametrize('circuit_param, expected', [
        (circuit(), {'_qubits':[0,1,2],'_moments':[],'name':'test_circuit'}),])
def test_creating_circuit(circuit_param,expected):
    # check class parameters
    assert circuit_param.__dict__ == expected

@pytest.mark.parametrize('circuit_param, expected', [
        (circuit(), {'_qubits':[0,1,2],'_moments':[],'name':'test_circuit'}),])
def test_add_moment(circuit_param,expected):
    # check class parameters
    assert circuit_param.__dict__ == expected
