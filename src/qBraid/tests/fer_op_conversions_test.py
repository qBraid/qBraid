# -*- coding: utf-8 -*-
# All rights reserved-2019©. 
import unittest
import numpy as np
from openfermion.ops import FermionOperator, InteractionOperator
from openfermion.utils import count_qubits
from qiskit.quantum_info import Pauli
from qiskit.aqua.operators import WeightedPauliOperator
from qBraid.conversions.qub_op_conversion import convert
from openfermion.chem import MolecularData
from openfermion.transforms import get_fermion_operator, jordan_wigner
from openfermion.linalg import get_ground_state, get_sparse_operator
import numpy
import scipy
import scipy.linalg


class convert_fer_op_test(unittest.TestCase):

    def test_of_qk(self):
        of_test_op_1 = QubitOperator(((0, 'Z'),(1, 'Z'),(2, 'Z'),(3, 'Z')), 1.0)
        correct_u_1 = np.array([1, 1, 1, 1])
        correct_v_1 = np.array([0, 0, 0, 0])
        correct_pauli_1 = Pauli(correct_u_1,correct_v_1)
        
        correct_op_1 = WeightedPauliOperator(paulis=[[1., correct_pauli_1]])
        x=convert(of_test_op_1)
        
        # Load saved file for LiH.
        diatomic_bond_length = 1.45
        geometry = [('Li', (0., 0., 0.)), ('H', (0., 0., diatomic_bond_length))]
        basis = 'sto-3g'
        multiplicity = 1

        # Set Hamiltonian parameters.
        active_space_start = 1
        active_space_stop = 3

        # Generate and populate instance of MolecularData.
        molecule = MolecularData(geometry, basis, multiplicity, description="1.45")
        molecule.load()

        # Get the Hamiltonian in an active space.
        molecular_hamiltonian = molecule.get_molecular_hamiltonian(
            occupied_indices=range(active_space_start),
            active_indices=range(active_space_start, active_space_stop))

        # Map operator to fermions and qubits.
        fermion_hamiltonian = get_fermion_operator(molecular_hamiltonian)
        qubit_hamiltonian = jordan_wigner(fermion_hamiltonian)
        qubit_hamiltonian.compress()
        print('The Jordan-Wigner Hamiltonian in canonical basis follows:\n{}'.format(qubit_hamiltonian))

        # Get sparse operator and ground state energy.
        sparse_hamiltonian = get_sparse_operator(qubit_hamiltonian)
        energy, state = get_ground_state(sparse_hamiltonian)
        print('Ground state energy before rotation is {} Hartree.\n'.format(energy))

        # Randomly rotate.
        n_orbitals = molecular_hamiltonian.n_qubits // 2
        n_variables = int(n_orbitals * (n_orbitals - 1) / 2)
        numpy.random.seed(1)
        random_angles = numpy.pi * (1. - 2. * numpy.random.rand(n_variables))
        kappa = numpy.zeros((n_orbitals, n_orbitals))
        index = 0
        for p in range(n_orbitals):
            for q in range(p + 1, n_orbitals):
                kappa[p, q] = random_angles[index]
                kappa[q, p] = -numpy.conjugate(random_angles[index])
                index += 1

            # Build the unitary rotation matrix.
            difference_matrix = kappa + kappa.transpose()
            rotation_matrix = scipy.linalg.expm(kappa)

            # Apply the unitary.
            molecular_hamiltonian.rotate_basis(rotation_matrix)

        # Get qubit Hamiltonian in rotated basis.
        qubit_hamiltonian = jordan_wigner(molecular_hamiltonian)
        qubit_hamiltonian.compress()
        print('The Jordan-Wigner Hamiltonian in rotated basis follows:\n{}'.format(qubit_hamiltonian))

        # Get sparse Hamiltonian and energy in rotated basis.
        sparse_hamiltonian = get_sparse_operator(qubit_hamiltonian)
        energy, state = get_ground_state(sparse_hamiltonian)
        print('Ground state energy after rotation is {} Hartree.'.format(energy))
        
        self.assertTrue(correct_op_1 == convert(of_test_op_1))
        self.assertTrue(correct_op_3 == convert(of_test_op_3))
        self.assertTrue(correct_op_4 == convert(of_test_op_4))
        self.assertTrue(correct_op_5 == convert(of_test_op_5))    
        self.assertTrue(correct_op_6 == convert(of_test_op_6))
        self.assertTrue(correct_op_7 == convert(of_test_op_7))

    def test_qis_of(self):
        qis_u_1 = np.array([1, 1, 1, 1, 0])
        qis_v_1 = np.array([0, 0, 0, 0, 0])
        qis_u_2 = np.zeros(5)
        qis_v_2 = np.zeros(5)
        qis_u_3 = np.array([0, 1, 1, 0, 0])
        qis_v_3 = np.array([1, 1, 0, 0, 0])
        qis_u_4 = np.zeros(4)
        qis_v_4 = np.ones(4)
        qis_u_5 = np.ones(4)
        qis_v_5 = np.ones(4)
        
        qis_pauli_1 = Pauli(qis_u_1,qis_v_1)
        qis_pauli_2 = Pauli(qis_u_2,qis_v_2)
        qis_pauli_3 = Pauli(qis_u_3,qis_v_3)
        qis_pauli_4 = Pauli(qis_u_4,qis_v_4)
        qis_pauli_5 = Pauli(qis_u_5,qis_v_5)
        
        qis_test_op_1 = WeightedPauliOperator(paulis=[[1., qis_pauli_1]])
        qis_test_op_2 = WeightedPauliOperator(paulis=[[1., qis_pauli_2]])
        qis_test_op_3 = WeightedPauliOperator(paulis=[[1., qis_pauli_3]])
        qis_test_op_4 = WeightedPauliOperator(paulis=[[1., qis_pauli_4]])
        qis_test_op_5 = WeightedPauliOperator(paulis=[[1., qis_pauli_5]])
        qis_test_op_6 = qis_test_op_1 + qis_test_op_3
        qis_test_op_7 = qis_test_op_2 + qis_test_op_3
        correct_op_1 = QubitOperator(((0, 'Z'),(1, 'Z'),(2, 'Z'),(3, 'Z')),1.0)
        correct_op_3 = QubitOperator(((0, 'X'),(1, 'Y'),(2, 'Z')),1.0)
        correct_op_4 = QubitOperator(((0, 'X'),(1, 'X'),(2, 'X'),(3, 'X')),1.0)
        correct_op_5 = QubitOperator(((0, 'Y'),(1, 'Y'),(2, 'Y'),(3, 'Y')),1.0)
        correct_op_6 = correct_op_1 + correct_op_3
        correct_op_7 = QubitOperator.identity() + correct_op_3
        self.assertTrue(correct_op_1 == convert(qis_test_op_1,'OPENFERMION'))
        self.assertTrue(correct_op_3 == convert(qis_test_op_3,'OPENFERMION'))
        self.assertTrue(correct_op_4 == convert(qis_test_op_4,'OPENFERMION'))
        self.assertTrue(correct_op_5 == convert(qis_test_op_5,'OPENFERMION'))
        self.assertTrue(correct_op_6 == convert(qis_test_op_6,'OPENFERMION'))
        self.assertTrue(correct_op_7 == convert(qis_test_op_7,'OPENFERMION'))

if __name__=='__main__':
    unittest.main()