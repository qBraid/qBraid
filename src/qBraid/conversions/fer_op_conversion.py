# -*- coding: utf-8 -*-
# All rights reserved-2020©. 

import numpy as np
from openfermion.ops import QubitOperator, FermionOperator, InteractionOperator
# from openfermion
from openfermion.transforms import get_interaction_operator
from openfermion.utils import count_qubits
from qiskit.quantum_info import Pauli
from qiskit.aqua.operators import WeightedPauliOperator
from qiskit.chemistry import FermionicOperator
from qiskit.chemistry.core import Hamiltonian

def convert(fer_int_op, output_type='QISKIT'):
    """Convert the fermion_operator between the various types available
    in 
    Args:
        fer_int_op: FermionicOperator class in qiskit-aqua or interactionoperator class in openfermion   
        output_fo_type (string): string for specifying the return package type for
                                qubit_operator 
    Returns:
        fermion_operator class in the requested package 
    """
    if isinstance(fer_int_op, InteractionOperator):
        if output_type == 'QISKIT':
            # OF_inter_oper = molecular_hamiltonian
            h1 = fer_int_op.one_body_tensor
            h2 = fer_int_op.two_body_tensor
            h2= np.einsum('ikmj->ijkm', h2)
            import inspect
            # print(inspect.getmembers(OF_inter_oper))
            # print(type(h2))
            # print(type(h1))
            fer_op_qiskit = FermionicOperator(h1, h2)
            
            return fer_op_qiskit
        elif output_qo_type == 'OPENFERMION':
            pass
            

    elif isinstance(fer_int_op, FermionicOperator) :
        if output_type=='OPENFERMION':
            h1 = fer_int_op.h1
            h2 = fer_int_op.h2
            import inspect
            # print(fer_int_op.)
            of_int_op = InteractionOperator(0.,h1,h2)
            of_fer_op = get_fermion_operator(of_int_op)
            print(of_fer_op)
            return of_fer_op
            
            
    elif isinstance(qubit_operator, QubitOperator) :
        pass
    else:
        raise TypeError('Input must be an one of the QubitOperators')


if __name__ == "__main__":
    from openfermion.hamiltonians import MolecularData
    from openfermion.transforms import get_fermion_operator, get_sparse_operator, jordan_wigner, get_interaction_operator
    from openfermion.utils import get_ground_state
    import numpy
    diatomic_bond_length = .7414
    geometry = [('H', (0., 0., 0.)), ('H', (0., 0., diatomic_bond_length))]
    basis = 'sto-3g'
    multiplicity = 1
    charge = 0
    description = str(diatomic_bond_length)
    molecule = MolecularData(geometry, basis, multiplicity,
                            charge, description)
    molecule.load()
    # Get the Hamiltonian in an active space.
    molecular_hamiltonian = molecule.get_molecular_hamiltonian()

    # 2.Using the integrals obtained from pyscf, to transform
    # the Hamiltonian from second quantization formalism to qubit operators.
    fermion_hamiltonian = get_fermion_operator(molecular_hamiltonian)
    mol_int_op = get_interaction_operator(fermion_hamiltonian)
    print(type(mol_int_op))
    print(type(molecular_hamiltonian))
    # print(mol_i/nt_op.one_body_tensor==molecular_hamiltonian.one_body_tensor)
    # print(mol_int_op.two_body_tensor==molecular_hamiltonian.two_body_tensor)
    # print(molecular_hamiltonian.two_body_tensor-mol_int_op.two_body_tensor)
    # print(mol_int_op==molecular_hamiltonian)
    qubit_hamiltonian = jordan_wigner(fermion_hamiltonian)
    qubit_hamiltonian.compress()
    # exit()
    # print('The Jordan-Wigner Hamiltonian in canonical basis follows:\n{}'.format(qubit_hamiltonian))

    # 3. exact diagonalize the matrix form of the qubit operator
    sparse_hamiltonian = get_sparse_operator(qubit_hamiltonian)
    energy, state = get_ground_state(sparse_hamiltonian)
    print('Ground state energy before rotation is {} Hartree.\n'.format(energy))
    convert(molecular_hamiltonian)

    import numpy as np
    from qiskit.chemistry.drivers import PySCFDriver
    from qiskit.aqua.algorithms import NumPyEigensolver as EE
    from qiskit.chemistry import FermionicOperator

    molecule = 'H .0 .0 0.0;H .0 .0 0.7414'
    driver = PySCFDriver(atom=molecule, basis='sto3g')
    qmolecule = driver.run()
    one_b = qmolecule.one_body_integrals
    two_b = qmolecule.two_body_integrals


    fer_op = FermionicOperator(h1=one_b, h2=two_b)
    convert(fer_op,'OPENFERMION')
    