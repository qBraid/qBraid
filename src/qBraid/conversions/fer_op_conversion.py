# -*- coding: utf-8 -*-
# All rights reserved-2020©. 

import numpy as np
from openfermion.ops import QubitOperator, FermionOperator, InteractionOperator
from openfermion.transforms import get_interaction_operator()
from openfermion.utils import count_qubits
from qiskit.quantum_info import Pauli
from qiskit.aqua.operators import WeightedPauliOperator
from qiskit.chemistry import FermionicOperator
from qiskit.chemistry.core import Hamiltonian

def convert(fermion_operator, output_qo_type='QISKIT'):
    """Convert the fermion_operator between the various types available
    in 
    Args:
        fermion_operator class: in either qiskit-aqua or openfermion   
        output_fo_type (string): string for specifying the return package type for
                                qubit_operator 
    Returns:
        fermion_operator class in the requested package 
    """
    if isinstance(fermion_operator, FermionOperator):
        if output_qo_type == 'QISKIT':
            OF_inter_oper = fermion_operator.get
            num_qubits = count_qubits(qubit_operator)
            output_qub_op = WeightedPauliOperator(paulis=[[0, Pauli.from_label('I' * num_qubits)]])
            for term, coeff in qubit_operator.terms.items():
                z = np.zeros(num_qubits)
                x = np.zeros(num_qubits)
                for gate in list(term):
                    if gate[1]=='X':
                        x[gate[0]]=1
                    elif gate[1]=='Z':
                        z[gate[0]]=1
                    elif gate[1]=='Y':
                        x[gate[0]]=1
                        z[gate[0]]=1
                output_qub_op += WeightedPauliOperator(paulis=[[coeff,Pauli(z=z,x=x)]])
            return output_qub_op
        elif output_qo_type == 'OPENFERMION':
            pass
            

    elif isinstance(qubit_operator, WeightedPauliOperator) :
        if output_qo_type == 'OPENFERMION':
            num_qubits = qubit_operator.num_qubits
            output_qub_op = QubitOperator()
            for term in qubit_operator._paulis:
                coeff = term[0]
                wpo_pauli = term[1]
                z = wpo_pauli._z
                x = wpo_pauli._x
                of_term = []
                for i in range(num_qubits):
                    if x[i] and z[i]:
                        of_term.append((i, 'Y'))
                    elif x[i]:
                        of_term.append((i, 'X'))
                    elif z[i]:
                        of_term.append((i, 'Z'))
                    else:
                        pass
                output_qub_op += QubitOperator(tuple(of_term), coeff)
            return output_qub_op
        elif output_qo_type=='PYQUIL':
            pass
            
    elif isinstance(qubit_operator, QubitOperator) :
        pass
    else:
        raise TypeError('Input must be an one of the QubitOperators')
        