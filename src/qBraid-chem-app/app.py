# -*- coding: utf-8 -*-
# All rights reserved-2020©. 

import numpy as np
from qiskit import QuantumCircuit, ClassicalRegister, QuantumRegister, execute
from pyscf import gto

class classical_calc_output():
    def __init__(self,molecule_name, geometry, basis, library):
        self.molecule_name = molecule_name
        self.geometry = geometry
        self.basis = basis
        self.library = library
        self.one_body_integrals = None
        self.two_body_integrals = None
        self.pyscf_result_object = None
        self.qiskit_hamiltonian_object = None
        



class quantum_calc_output():
    def __init__(self,molecule_name, geometry, basis, library):
        self.molecule_name = molecule_name
        self.geometry = geometry
        self.basis = basis
        self.library = library


def classical_cal(library='pyscf', molecule_name='', geometry='H 0 0 0; H 0 0 1',
                    basis = 'sto-3g', method='HF'):
    
    # Inputs for pyscf that we may want to include
    if library=='pyscf':
        pyscf_code_run(molecule_name, geometry,basis,method):
    elif library=='qiskit':
        pass
    elif library=='psi4':
        pass
    elif library=='openfermion':
        pass
    elif gaussian:
        pass
    else:
        raise
    
    # mol = gto.Mole()
    # mol.verbose = 5
    # mol.output = 'h2.log'
    # mol.atom = 'H 0 0 0; H 0 0 1'
    # mol.basis = 'sto-3g'


def pyscf_code_run(molecule_name,geometry,basis,method):
    from pyscf import gto, scf

    mol = gto.Mole()
    mol.verbose = 5
    mol.output = molecule_name+'.log'
    mol.atom = geometry
    mol.basis = basis
    
    # Specifying extra features. Will be part of future releases.
    # mol.basis = {'O': 'sto-3g', 'H': 'cc-pvdz', 'H@2': '6-31G'}
    # mol.symmetry = 1
    # mol.charge = 1
    # mol.spin = 1
    # mol.nucmod = {'O1': 1}
    # mol.mass = {'O1': 18, 'H': 2}


    classical_output = classical_calc_output(molecule_name, geometry, basis, library)
    
    if method == 'RHF':
        scf_setup = scf.RHF(mol)
    elif method=='UHF':
        scf_setup = scf.UHF(mol):
    elif method=='ROHF':
        scf_setup = scf.ROHF(mol)
    else:
        scf_setup = scf.RHF(mol)
    
    # part of future release
    # scf_setup.conv_tol = conv_tol
    # scf_setup.max_cycle = max_cycle
    # scf_setup.init_guess = init_guess
    
    ehf = scf_setup.kernel()
    if isinstance(scf_setup.mo_coeff, tuple):
        mo_coeff = scf_setup.mo_coeff[0]
        mo_coeff_b = scf_setup.mo_coeff[1]
        # mo_occ   = scf_setup.mo_occ[0]
        # mo_occ_b = scf_setup.mo_occ[1]
    else:
        if len(scf_setup.mo_coeff.shape) > 2:
            mo_coeff = scf_setup.mo_coeff[0]
            mo_coeff_b = scf_setup.mo_coeff[1]
            # mo_occ   = scf_setup.mo_occ[0]
            # mo_occ_b = scf_setup.mo_occ[1]
        else:
            mo_coeff = scf_setup.mo_coeff
            mo_coeff_b = None
            # mo_occ   = mf.mo_occ
            # mo_occ_b = None
    norbs = mo_coeff.shape[0]

    if isinstance(scf_setup.mo_energy, tuple):
        orbs_energy = scf_setup.mo_energy[0]
        orbs_energy_b = scf_setup.mo_energy[1]
    else:
        # See PYSCF 1.6.2 comment above - this was similarly changed
        if len(scf_setup.mo_energy.shape) > 1:
            orbs_energy = scf_setup.mo_energy[0]
            orbs_energy_b = scf_setup.mo_energy[1]
        else:
            orbs_energy = scf_setup.mo_energy
            orbs_energy_b = None

    hij = scf_setup.get_hcore()
    mohij = np.dot(np.dot(mo_coeff.T, hij), mo_coeff)
    mohij_b = None
    if mo_coeff_b is not None:
        mohij_b = np.dot(np.dot(mo_coeff_b.T, hij), mo_coeff_b)

    eri = mol.intor('int2e', aosym=1)
    mo_eri = ao2mo.incore.full(scf_setup._eri, mo_coeff, compact=False)
    mohijkl = mo_eri.reshape(norbs, norbs, norbs, norbs)

    if mohij_b is None:
            mohij_b = mohij

        # The number of spin orbitals is twice the number of orbitals
        norbs = mohij.shape[0]
        nspin_orbs = 2*norbs

        # One electron terms
        moh1_qubit = numpy.zeros([nspin_orbs, nspin_orbs])
        for p in range(nspin_orbs):  # pylint: disable=invalid-name
            for q in range(nspin_orbs):
                spinp = int(p/norbs)
                spinq = int(q/norbs)
                if spinp % 2 != spinq % 2:
                    continue
                ints = mohij if spinp == 0 else mohij_b
                orbp = int(p % norbs)
                orbq = int(q % norbs)
                if abs(ints[orbp, orbq]) > threshold:
                    moh1_qubit[p, q] = ints[orbp, orbq]

    one_body_integral = moh1_qubit


    norbs = mohijkl.shape[0]
    nspin_orbs = 2*norbs
    moh2_qubit = numpy.zeros([nspin_orbs, nspin_orbs, nspin_orbs, nspin_orbs])
    ints_aa = numpy.einsum('ijkl->ljik', mohijkl)
    ints_bb = ints_ba = ints_ab = ints_aa
    # The number of spin orbitals is twice the number of orbitals
    norbs = mohijkl.shape[0]
    nspin_orbs = 2*norbs

    # Two electron terms
    moh2_qubit = numpy.zeros([nspin_orbs, nspin_orbs, nspin_orbs, nspin_orbs])
    for p in range(nspin_orbs):  # pylint: disable=invalid-name
        for q in range(nspin_orbs):
            for r in range(nspin_orbs):
                for s in range(nspin_orbs):  # pylint: disable=invalid-name
                    spinp = int(p/norbs)
                    spinq = int(q/norbs)
                    spinr = int(r/norbs)
                    spins = int(s/norbs)
                    if spinp != spins:
                        continue
                    if spinq != spinr:
                        continue
                    if spinp == 0:
                        ints = ints_aa if spinq == 0 else ints_ba
                    else:
                        ints = ints_ab if spinq == 0 else ints_bb
                    orbp = int(p % norbs)
                    orbq = int(q % norbs)
                    orbr = int(r % norbs)
                    orbs = int(s % norbs)
                    if abs(ints[orbp, orbq, orbr, orbs]) > threshold:
                        moh2_qubit[p, q, r, s] = -0.5*ints[orbp, orbq, orbr, orbs]
  
    # Create driver level molecule object and populate
    _q_ = QMolecule()
    _q_.origin_driver_version = pyscf_version
    # Energies and orbits
    _q_.hf_energy = ehf
    _q_.nuclear_repulsion_energy = enuke
    _q_.num_orbitals = norbs
    _q_.num_alpha = mol.nelec[0]
    _q_.num_beta = mol.nelec[1]
    _q_.mo_coeff = mo_coeff
    _q_.mo_coeff_b = mo_coeff_b
    # 1 and 2 electron integrals AO and MO
    _q_.hcore = hij
    _q_.hcore_b = None
    _q_.kinetic = mol.intor_symmetric('int1e_kin')
    _q_.overlap = scf_setup.get_ovlp()
    _q_.eri = eri
    _q_.mo_onee_ints = mohij
    _q_.mo_onee_ints_b = mohij_b
    _q_.mo_eri_ints = mohijkl
    _q_.mo_eri_ints_bb = mohijkl_bb
    _q_.mo_eri_ints_ba = mohijkl_ba
    # dipole integrals AO and MO
    

def pyscf_code_print(molecule_name,geometry,basis,method):
    code_string = '''from pyscf import gto
    mol = gto.Mole()
    mol.verbose = 5
    mol.output = '''+molecule_name+'''.log
    mol.atom = '''+str(geometry)+'''
    mol.basis = '''+basis
    return code_string

def qiskit_code_run(molecule_name,geometry,basis,method):
    import numpy as np
    from qiskit.chemistry.drivers import PySCFDriver, HFMethodType
    from qiskit.aqua.algorithms import ExactEigensolver as EE
    from qiskit.chemistry import FermionicOperator

    driver = PySCFDriver(atom=molecule, basis='sto3g',hf_method=HFMethodType.RHF,)
    qmolecule = driver.run()
    one_b = qmolecule.one_body_integrals
    two_b = qmolecule.two_body_integrals

    pass

def qiskit_code_print(molecule_name,geometry,basis,method):
    pass



mol.symmetry = 1
mol.charge = 1
mol.spin = 1
mol.nucmod = {'O1': 1}
mol.mass = {'O1': 18, 'H': 2}


# finally building the molecule after



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
