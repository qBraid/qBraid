# -*- coding: utf-8 -*-
# All rights reserved-2019©.
import copy

# SET BACKEND
import matplotlib as mpl
import numpy as np
from openfermion.chem import MolecularData
from openfermion.linalg import eigenspectrum
from openfermion.ops import InteractionOperator
from openfermion.transforms import get_fermion_operator, jordan_wigner
from qiskit.aqua.algorithms import NumPyEigensolver as EE
from qiskit.chemistry import FermionicOperator
from qiskit.chemistry.drivers import PySCFDriver

from qbraid.operators.conversions.fer_op_conversion import convert

mpl.use("TkAgg")


def test_fer_op_H2_of_qk():
    # Initializing fermionic Hamiltonian in openfermion
    diatomic_bond_length = 0.7414
    geometry = [("H", (0.0, 0.0, 0.0)), ("H", (0.0, 0.0, diatomic_bond_length))]
    basis = "sto-3g"
    multiplicity = 1
    charge = 0
    description = str(diatomic_bond_length)
    molecule = MolecularData(geometry, basis, multiplicity, charge, description)
    molecule.load()

    molecular_hamiltonian = molecule.get_molecular_hamiltonian()
    fermion_hamiltonian = get_fermion_operator(molecular_hamiltonian)
    int_op = InteractionOperator(
        constant=molecular_hamiltonian.constant,
        one_body_tensor=molecular_hamiltonian.one_body_tensor,
        two_body_tensor=molecular_hamiltonian.two_body_tensor,
    )
    # Using qBraid convert function
    qiskit_fer_op = convert(fermion_hamiltonian)
    qiskit_fer_op1 = convert(int_op)
    qiskit_qub_op = qiskit_fer_op.mapping("jordan_wigner")
    qiskit_qub_op1 = qiskit_fer_op1.mapping("jordan_wigner")
    evals = EE(qiskit_qub_op, k=16).run()
    evals1 = EE(qiskit_qub_op, k=16).run()

    molecule = "H .0 .0 0.0;H .0 .0 .7414"
    driver = PySCFDriver(atom=molecule, basis="sto3g")
    qmolecule = driver.run()
    one_b = qmolecule.one_body_integrals
    two_b = qmolecule.two_body_integrals
    fer_op = FermionicOperator(one_b, two_b)
    qiskit_qub_op_ref = fer_op.mapping("jordan_wigner")
    evals_correct = EE(qiskit_qub_op, k=16).run()
    assert np.all(np.real(evals_correct.eigenvalues) == np.real(evals.eigenvalues))
    assert np.all(np.real(evals_correct.eigenvalues) == np.real(evals1.eigenvalues))


def test_fer_op_H2_qk_of():
    molecule = "H .0 .0 0.0;H .0 .0 0.7414"
    driver = PySCFDriver(atom=molecule, basis="sto3g")
    qmolecule = driver.run()
    one_b = qmolecule.one_body_integrals
    two_b = qmolecule.two_body_integrals
    fer_op = FermionicOperator(h1=one_b, h2=two_b)
    fer_op_of = convert(fer_op, "OPENFERMION")
    qub_op_of = jordan_wigner(fer_op_of)
    es_of = eigenspectrum(qub_op_of)

    diatomic_bond_length = 0.7414
    geometry = [("H", (0.0, 0.0, 0.0)), ("H", (0.0, 0.0, diatomic_bond_length))]
    basis = "sto-3g"
    multiplicity = 1
    charge = 0
    description = str(diatomic_bond_length)
    molecule = MolecularData(geometry, basis, multiplicity, charge, description)
    molecule.load()

    molecular_hamiltonian = molecule.get_molecular_hamiltonian()
    fermion_hamiltonian = get_fermion_operator(molecular_hamiltonian)
    fermion_hamiltonian = fermion_hamiltonian
    qub_op = jordan_wigner(fermion_hamiltonian)
    es_correct = eigenspectrum(qub_op)
    assert np.all(
        np.round(es_correct, 7) == np.round(es_of + np.ones(np.shape(es_of)) * 0.71375399, 7)
    )


# is this random_hams_of_qiskit necessary?
def random_hams_of_qiskit(self):
    one_b_list = self.get_rand_one_b_tensors()
    two_b_list = self.get_rand_two_b_tensors()


def get_rand_one_b_tensors():
    one_body_0 = np.zeros([4, 4])
    one_body_1 = np.array([[0.4, 0, 0, 0], [0, 0.5, 0, 0], [0, 0, 0.6, 0], [0, 0, 0, 0.7]])
    one_body_2 = np.array([[1, 2, 0, 3], [2, 1, 2, 0], [0, 2, 1, 2.5], [3, 0, 2.5, 1]])
    one_body_3 = np.array([[1, 2, 0, 3], [2, 1, 2, 0], [0, 2, 1, 2.5], [3, 0, 2.5, 1]])
    one_body_4 = np.array(
        [[1.1, 2, 1.5, 3], [2, 1.2, 2, 1.3], [1.5, 2, 1.3, 2.5], [3, 1.3, 2.5, 1.4]]
    )
    one_body_5 = np.random.rand(4, 4)
    one_body_5 = one_body_5 + one_body_5.T
    one_body_6 = np.random.rand(4, 4)
    one_body_6 = one_body_6 + one_body_6.T
    one_body_7 = np.random.rand(4, 4)
    one_body_7 = one_body_7 + one_body_7.T
    one_body_8 = np.random.rand(4, 4)
    one_body_8 = one_body_8 + one_body_8.T
    one_body_tensor_list = []
    for i in range(8):
        one_body_tensor_list.append(eval("one_body_" + str(i)))
    return one_body_tensor_list


def get_rand_two_b_tensors():
    two_body_0 = np.zeros([4, 4, 4, 4])
    # initiating number operator terms for all the possible cases
    two_body_1 = copy.deepcopy(two_body_0)
    two_body_1[(1, 2, 3, 1)] = 0.3
    two_body_1[(1, 3, 2, 1)] = 0.3
    two_body_2 = copy.deepcopy(two_body_1)
    two_body_2[(1, 2, 1, 3)] = 0.25
    two_body_2[(3, 1, 2, 1)] = 0.25
    two_body_3 = copy.deepcopy(two_body_2)
    two_body_3[(0, 2, 2, 1)] = 0.69
    two_body_3[(1, 2, 2, 0)] = 0.69
    two_body_4 = copy.deepcopy(two_body_3)
    two_body_4[(1, 2, 3, 2)] = 1.1
    two_body_4[(2, 3, 2, 1)] = 1.1
    two_body_5 = copy.deepcopy(two_body_4)
    two_body_5[(2, 2, 2, 2)] = 0.3
    two_body_6 = copy.deepcopy(two_body_5)
    two_body_6[(1, 2, 1, 2)] = 0.3
    two_body_6[(2, 1, 2, 1)] = 0.3
    two_body_7 = copy.deepcopy(two_body_6)
    two_body_7[(0, 1, 2, 3)] = 1.39
    two_body_7[(3, 2, 1, 0)] = 1.39
    two_body_8 = copy.deepcopy(two_body_7)
    two_body_8[(0, 1, 1, 3)] = 0.59
    two_body_8[(3, 1, 1, 0)] = 0.59
    two_body_tensor_list = []
    for i in range(8):
        two_body_tensor_list.append(eval("two_body_" + str(i)))
    return two_body_tensor_list


def test_fer_op_LiH_qk_of():
    bond_length = 1.45
    geometry = [("Li", (0.0, 0.0, 0.0)), ("H", (0.0, 0.0, bond_length))]
    basis = "sto-3g"
    multiplicity = 1
    charge = 0
    description = str(bond_length)
    molecule = MolecularData(geometry, basis, multiplicity, charge, description)
    molecule.load()
    molecular_ham = molecule.get_molecular_hamiltonian()
    fermion_hamiltonian = get_fermion_operator(molecular_ham)
    fer_op_qiskit = convert(fermion_hamiltonian)
    qub_op_qiskit = fer_op_qiskit.mapping("jordan_wigner")
    evals = EE(qub_op_qiskit, k=8).run()

    molecule = "Li .0 .0 0.0;H .0 .0 1.45"
    # molecule = 'H .0 .0 0.0;H .0 .0 .7414'
    driver = PySCFDriver(atom=molecule, basis="sto3g")
    qmolecule = driver.run()
    one_b = qmolecule.one_body_integrals
    two_b = qmolecule.two_body_integrals
    fer_op = FermionicOperator(one_b, two_b)
    fer_op._convert_to_interleaved_spins()
    qub_op = fer_op.mapping("jordan_wigner")
    evals_correct = EE(qub_op, k=8).run()
    assert np.all(
        np.round(np.real(evals.eigenvalues), 7) == np.round(np.real(evals_correct.eigenvalues), 7)
    )


if __name__ == "__main__":
    print("FERMION OPERATOR TESTS")
    print("-" * 100)
    print()
    test_fer_op_H2_of_qk()  # passes
    test_fer_op_LiH_qk_of()
    print("-" * 100)
    print()

    print("ALL TESTS PASSED")
