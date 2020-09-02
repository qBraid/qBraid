# -*- coding: utf-8 -*-
# All rights reserved-2020©. 

import numpy as np
from qiskit import QuantumCircuit, ClassicalRegister, QuantumRegister, execute
from pyscf import gto

def classical_cal(geometry='H 0 0 0; H 0 0 1',basis = 'sto-3g';)

mol = gto.Mole()
mol.verbose = 5
mol.output = 'h2.log'
mol.atom = 'H 0 0 0; H 0 0 1'
mol.basis = 'sto-3g'
mol.build()
from pyscf import scf
m = scf.RHF(mol)
print('E(HF) = %g' % m.kernel())


# ++++++++++++++++++++++++++++++
# Running using qiskit and its drivers
# +++++++++++++++++++++++++++++++++++

# Importing the packages
import numpy as np
# Importing the driver that lets us access pyscf from qiskit
from qiskit.chemistry.drivers import PySCFDriver
# Importing the function for exact diagonalization
from qiskit.aqua.algorithms import ExactEigensolver as EE
# Import the class fermionicoperator
from qiskit.chemistry import FermionicOperator

# 1. Setting up the system in pyscf and running Hartree-Fock calculation.
# Define the molecule
molecule = 'H .0 .0 0.0;H .0 .0 0.7414'
# Setup the pyscf driver in qiskit
driver = PySCFDriver(atom=molecule, basis='sto3g')
# Run the pyscf driver
qmolecule = driver.run()
# get the one-body and two-body integrals
one_b = qmolecule.one_body_integrals
two_b = qmolecule.two_body_integrals


# 2.Using the integrals obtained from pyscf, to transform
# the Hamiltonian from second quantization formalism to qubit operators.
fer_op = FermionicOperator(h1=one_b, h2=two_b)
# transform the fermionic operator to qubit operator
qubit_op = fer_op.mapping('jordan_wigner')



ferOp = FermionicOperator(h1=molecule.one_body_integrals, h2=molecule.two_body_integrals)
qubitOp = ferOp.mapping(map_type='JORDAN_WIGNER', threshold=0.00000001)
qubitOp.chop(10**-10)

# Using exact eigensolver to get the smallest eigenvalue
exact_eigensolver = NumPyMinimumEigensolver(qubitOp)
ret = exact_eigensolver.run()
print('The exact ground state energy is: {}'.format(ret.eigenvalue.real))






# 3. exact diagonalize the matrix form of the qubit operator
result = EE(qubit_op).run()
lines, result = operator.process_algorithm_result(result)
energies = result['energy']
hf_energies = result['hf_energy']  # Independent of algorithm & mapping

# print('One body integrals:', one_b)
# print('Two body integrals:', two_b)
print(qubit_op.print_operators())
print('Distance: ', 0.7414)
print('Energy:', energies)
print('Hartree-Fock energy', hf_energies)


# ++++++++++++++++++++++++++++++
# Running using openfermion and openfermion-pyscf-plugin
# +++++++++++++++++++++++++++++++++++
# Importing the relavant classes and functions
from openfermion.hamiltonians import MolecularData
from openfermion.transforms import get_fermion_operator, get_sparse_operator, jordan_wigner
from openfermion.utils import get_ground_state

# 1. Setting up the system in pyscf and running Hartree-Fock calculation.
# Define the molecule
diatomic_bond_length = .7414
geometry = [('H', (0., 0., 0.)), ('H', (0., 0., diatomic_bond_length))]
basis = 'sto-3g'
multiplicity = 1
charge = 0
description = str(diatomic_bond_length)

# Initialize the molecule
molecule = MolecularData(geometry, basis, multiplicity,
                         charge, description)
# Just like qiskit-chemistry openfermion uses pyscf, but    the calculation is done using
# a plugin and the results are stored and can be used later. The results for H2 are
# already present, so we can just use them.
molecule.load()


# Get the Hamiltonian in an active space.
molecular_hamiltonian = molecule.get_molecular_hamiltonian()

# 2.Using the integrals obtained from pyscf, to transform
# the Hamiltonian from second quantization formalism to qubit operators.
fermion_hamiltonian = get_fermion_operator(molecular_hamiltonian)
qubit_hamiltonian = jordan_wigner(fermion_hamiltonian)
qubit_hamiltonian.compress()
print('The Jordan-Wigner Hamiltonian in canonical basis follows:\n{}'.format(qubit_hamiltonian))

# 3. exact diagonalize the matrix form of the qubit operator
sparse_hamiltonian = get_sparse_operator(qubit_hamiltonian)
energy, state = get_ground_state(sparse_hamiltonian)
print('Ground state energy before rotation is {} Hartree.\n'.format(energy))
