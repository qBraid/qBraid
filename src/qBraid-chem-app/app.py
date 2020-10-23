# -*- coding: utf-8 -*-
# All rights reserved-2020©. 

import numpy as np
import numpy
from qiskit import QuantumCircuit, ClassicalRegister, QuantumRegister, execute
from pyscf import gto, ao2mo

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
        self.hf_energy = None


class quantum_calc_output():
    def __init__(self,molecule_name, geometry, basis, library):
        self.molecule_name = molecule_name
        self.geometry = geometry
        self.basis = basis
        self.library = library
        self.quantum_circ = None
        self.algo_name = None
        self.one_body_integrals = None
        self.two_body_integrals = None
        self.qubit_operator = None
        self.fermionic_operator = None
        



def classical_cal(library='pyscf', molecule_name='', geometry='H 0 0 0; H 0 0 .7414',
                    basis = 'sto-3g', method='HF', print_code=False):
    
    # Inputs for pyscf that we may want to include
    if library=='pyscf':
        if print_code:
            pyscf_code_print(molecule_name, geometry,basis,method)
        else:
            pyscf_code_run(molecule_name, geometry,basis,method)
    elif library=='qiskit':
        if print_code:
            qiskit_classical_code_print(molecule_name, geometry,basis,method)
        else:
            qiskit_classical_code_run(molecule_name, geometry,basis,method)
    elif library=='psi4':
        pass
    elif library=='openfermion':
        pass
    elif gaussian:
        pass
    else:
        raise
    


def quantum_calc(library='qiskit', mapping='jordan_wigner', 
                qubit_tapering=False,algorithm='EE',
                output='ground_state_energy', print_code=False):
    
    # Inputs for pyscf that we may want to include
    if library=='qiskit':
        if print_code:
            qiskit_quantum_code_print(mapping='jordan_wigner', 
                qubit_tapering=False,algorithm='EE',
                output='ground_state_energy')
        else:
            qiskit_quantum_code_run(mapping='jordan_wigner', 
                qubit_tapering=False,algorithm='EE',
                output='ground_state_energy')
    elif library=='openfermion':
        pass
    elif gaussian:
        pass
    else:
        raise

def pyscf_code_run(molecule_name,geometry,basis,method):
    from pyscf import gto, scf
    threshold =1e-12
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


    classical_output = classical_calc_output(molecule_name, geometry, basis, library='pyscf')
    mol.build()
    if method == 'RHF':
        scf_setup = scf.RHF(mol)
    elif method=='UHF':
        scf_setup = scf.UHF(mol)
    elif method=='ROHF':
        scf_setup = scf.ROHF(mol)
    else:
        scf_setup = scf.RHF(mol)
    
    # part of future release
    # scf_setup.conv_tol = conv_tol
    # scf_setup.max_cycle = max_cycle
    # scf_setup.init_guess = init_guess
    
    ehf = scf_setup.kernel()
    if len(scf_setup.mo_coeff.shape) > 2:
        mo_coeff = scf_setup.mo_coeff[0]
        mo_coeff_b = scf_setup.mo_coeff[1]
    else:
        mo_coeff = scf_setup.mo_coeff
        mo_coeff_b = None
    norbs = mo_coeff.shape[0]

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

    mohijkl_bb = None
    mohijkl_ba = None
    if mo_coeff_b is not None:
        mo_eri_b = ao2mo.incore.full(scf_setup._eri, mo_coeff_b, compact=False)
        mohijkl_bb = mo_eri_b.reshape(norbs, norbs, norbs, norbs)
        mo_eri_ba = ao2mo.incore.general(scf_setup._eri,
                                         (mo_coeff_b, mo_coeff_b, mo_coeff, mo_coeff),
                                         compact=False)
        mohijkl_ba = mo_eri_ba.reshape(norbs, norbs, norbs, norbs)

    #getting one body integrals

    if mohij_b is None:
        mohij_b = mohij

    # Spin orbitals are twice the number of spatial orbitals
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

    classical_output.one_body_integrals= moh1_qubit
    
    #Two electron terms
    ints_aa = numpy.einsum('ijkl->ljik', mohijkl)

    if mohijkl_bb is None or mohijkl_ba is None:
        ints_bb = ints_ba = ints_ab = ints_aa
    else:
        ints_bb = numpy.einsum('ijkl->ljik', mohijkl_bb)
        ints_ba = numpy.einsum('ijkl->ljik', mohijkl_ba)
        ints_ab = numpy.einsum('ijkl->ljik', mohijkl_ba.transpose())


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

    classical_output.two_body_integrals = moh2_qubit
    return classical_output
    
    # # Create driver level molecule object and populate
    # _q_ = QMolecule()
    # _q_.origin_driver_version = pyscf_version
    # # Energies and orbits
    # _q_.hf_energy = ehf
    # _q_.nuclear_repulsion_energy = enuke
    # _q_.num_orbitals = norbs
    # _q_.num_alpha = mol.nelec[0]
    # _q_.num_beta = mol.nelec[1]
    # _q_.mo_coeff = mo_coeff
    # _q_.mo_coeff_b = mo_coeff_b
    # # 1 and 2 electron integrals AO and MO
    # _q_.hcore = hij
    # _q_.hcore_b = None
    # _q_.kinetic = mol.intor_symmetric('int1e_kin')
    # _q_.overlap = scf_setup.get_ovlp()
    # _q_.eri = eri
    # _q_.mo_onee_ints = mohij
    # _q_.mo_onee_ints_b = mohij_b
    # _q_.mo_eri_ints = mohijkl
    # _q_.mo_eri_ints_bb = mohijkl_bb
    # _q_.mo_eri_ints_ba = mohijkl_ba
    # # dipole integrals AO and MO
    

def pyscf_code_print(molecule_name,geometry,basis,method):
    code_string = '''from pyscf import gto
    mol = gto.Mole()
    mol.verbose = 5
    mol.output = '''+molecule_name+'''.log
    mol.atom = '''+str(geometry)+'''
    mol.basis = '''+basis

    code_string=code_string+'''\n classical_output = classical_calc_output(molecule_name, geometry, basis, library)
    
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
    if len(scf_setup.mo_coeff.shape) > 2:
        mo_coeff = scf_setup.mo_coeff[0]
        mo_coeff_b = scf_setup.mo_coeff[1]
    else:
        mo_coeff = scf_setup.mo_coeff
        mo_coeff_b = None
    norbs = mo_coeff.shape[0]

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

    mohijkl_bb = None
    mohijkl_ba = None
    if mo_coeff_b is not None:
        mo_eri_b = ao2mo.incore.full(scf_setup._eri, mo_coeff_b, compact=False)
        mohijkl_bb = mo_eri_b.reshape(norbs, norbs, norbs, norbs)
        mo_eri_ba = ao2mo.incore.general(scf_setup._eri,
                                         (mo_coeff_b, mo_coeff_b, mo_coeff, mo_coeff),
                                         compact=False)
        mohijkl_ba = mo_eri_ba.reshape(norbs, norbs, norbs, norbs)

    #getting one body integrals

    if mohij_b is None:
        mohij_b = mohij

    # Spin orbitals are twice the number of spatial orbitals
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

    classical_calc_output.one_body_integrals= moh1_qubit
    
    #Two electron terms
    ints_aa = numpy.einsum('ijkl->ljik', mohijkl)

    if mohijkl_bb is None or mohijkl_ba is None:
        ints_bb = ints_ba = ints_ab = ints_aa
    else:
        ints_bb = numpy.einsum('ijkl->ljik', mohijkl_bb)
        ints_ba = numpy.einsum('ijkl->ljik', mohijkl_ba)
        ints_ab = numpy.einsum('ijkl->ljik', mohijkl_ba.transpose())


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

    classical_calc_output.two_body_integrals = moh2_qubit
    '''
    return code_string

def qiskit_classical_code_run(molecule_name,geometry,basis,method):
    import numpy as np
    from qiskit.chemistry.drivers import PySCFDriver, HFMethodType
    driver = PySCFDriver(atom=geometry, basis='sto3g',hf_method=HFMethodType.RHF,)
    qmolecule = driver.run()
    classical_output = classical_calc_output(molecule_name,geometry,basis,library='qiskit')
    classical_output.one_body_integrals = qmolecule.one_body_integrals
    classical_output.two_body_integrals = qmolecule.two_body_integrals
    return classical_output
    

def qiskit_classical_code_print(molecule_name,geometry,basis,method):
    pyscfdriver_code_string = 'PySCFDriver(atom='+molecule+', basis='+basis+',hf_method=HFMethodType.'+method+')'
    code_string = '''import numpy as np
    from qiskit.chemistry.drivers import PySCFDriver, HFMethodType
    driver ='''+pyscfdriver_code_string+'''
    qmolecule = driver.run()
    classical_output = classical_calc_output(molecule_name,geometry,basis,library)
    classical_output.one_body_integrals = qmolecule.one_body_integrals
    classical_output.two_body_integrals = qmolecule.two_body_integrals
    '''
    return code_string


def qiskit_quantum_code_run(classical_output, mapping='jordan_wigner',
                            qubit_tapering=False,run_vqe=True, vqe_config=None):
    one_b = classical_output.one_body_integrals
    two_b = classical_output.two_body_integrals
    fer_op = FermionicOperator(h1=one_b, h2=two_b)
    # transform the fermionic operator to qubit operator
    qubit_op = fer_op.mapping('jordan_wigner')
    if qubit_tapering:
        pass
    output = quantum_calc_output(classical_output.molecule_name,
                                 classical_output.geometry,
                                  classical_output.basis,library='qiskit')
    output.fermionic_operator = fer_op
    output.qubit_operator = qubit_op





def qiskit_quantum_code_print():
    pass

def openfermion_quantum_code_run():
    pass

def openfermion_quantum_code_print():
    pass

def run_cofiguration(quantum_calc_output, run_on_hardware=False, hardware_cofig=Nonce,
                    simulation_config=None):
    if run_on_hardware:
        pass
    else:
        if simulation_config is None:
            print('Please pass valid simulation configuration')
        else:
            if simulation_config['software_platform']=='IBM':
                if simulation_config['Noisy']:
                    pass
                else:
                    if simulation_config['simulator']=='statevector_simulator':
                        pass
                    elif simulation_config['simulator']=='qasm_simulator':
                        pass
                    elif simulation_config['simulator']=='unitary_simulator':
                        pass
            

if __name__ == "__main__":
    classical_cal()
    classical_cal(library='qiskit')