# -*- coding: utf-8 -*-
# All rights reserved-2019©. 
import unittest
import numpy as np
from openfermion.ops import FermionOperator, InteractionOperator
from openfermion.utils import count_qubits, get_ground_state
from qBraid.conversions.fer_op_conversion import convert

from openfermion.hamiltonians import MolecularData
from openfermion.transforms import get_fermion_operator,
         get_sparse_operator, jordan_wigner, get_interaction_operator
from openfermion.utils import get_ground_state

from qiskit.chemistry.drivers import PySCFDriver
from qiskit.aqua.algorithms import NumPyEigensolver as EE
from qiskit.chemistry import FermionicOperator

import numpy
import scipy
import scipy.linalg


class convert_fer_op_test(unittest.TestCase):
    def test_fer_op_H2_of_qk(self):
    # +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    #        Using H2 Hamiltonian to get Fermion operator in Openfermion
    # +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
        diatomic_bond_length = .7414
        geometry = [('H', (0., 0., 0.)), ('H', (0., 0., diatomic_bond_length))]
        basis = 'sto-3g'
        multiplicity = 1
        charge = 0
        description = str(diatomic_bond_length)
        molecule = MolecularData(geometry, basis, multiplicity,
                                charge, description)
        molecule.load()
        molecular_hamiltonian = molecule.get_molecular_hamiltonian()
        fermion_hamiltonian = get_fermion_operator(molecular_hamiltonian)
        mol_int_op = get_interaction_operator(fermion_hamiltonian)
        print(type(mol_int_op))
        print(type(molecular_hamiltonian))
        convert(molecular_hamiltonian)
        # Remove the following lines later.
        # print(mol_i/nt_op.one_body_tensor==molecular_hamiltonian.one_body_tensor)
        # print(mol_int_op.two_body_tensor==molecular_hamiltonian.two_body_tensor)
        # print(molecular_hamiltonian.two_body_tensor-mol_int_op.two_body_tensor)
        # print(mol_int_op==molecular_hamiltonian)
        qubit_hamiltonian = jordan_wigner(fermion_hamiltonian)
        qubit_hamiltonian.compress()
        # exit()
        # print('The Jordan-Wigner Hamiltonian in canonical basis follows:\n{}'.format(qubit_hamiltonian))
        sparse_hamiltonian = get_sparse_operator(qubit_hamiltonian)
        energy, state = get_ground_state(sparse_hamiltonian)
        # print('Ground state energy before rotation is {} Hartree.\n'.format(energy))


    def test_fer_op_H2_qk_of(self):
        molecule = 'H .0 .0 0.0;H .0 .0 0.7414'
        driver = PySCFDriver(atom=molecule, basis='sto3g')
        qmolecule = driver.run()
        one_b = qmolecule.one_body_integrals
        two_b = qmolecule.two_body_integrals


        fer_op = FermionicOperator(h1=one_b, h2=two_b)
        convert(fer_op)
    

    def test_fer_op_LiH_of_qk(self):
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
        # print('The Jordan-Wigner Hamiltonian in canonical basis follows:\n{}'.format(qubit_hamiltonian))

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
        
        # self.assertTrue(correct_op_1 == convert(of_test_op_1))
        
    def test_fer_op_LiH_qk_of(self):
        molecule = 'Li .0 .0 0.0;H .0 .0 1.45'
        driver = PySCFDriver(atom=molecule, basis='sto3g')
        qmolecule = driver.run()
        one_b = qmolecule.one_body_integrals
        two_b = qmolecule.two_body_integrals


if __name__=='__main__':
    unittest.main()