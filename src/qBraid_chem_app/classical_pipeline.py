import numpy as np
from qiskit.chemistry.drivers import PySCFDriver, HFMethodType
from qiskit import QuantumCircuit, ClassicalRegister, QuantumRegister, execute
from qiskit.aqua.operators import Z2Symmetries
from pyscf import gto, ao2mo
import numpy

import os

from openfermion.hamiltonians import MolecularData

import openfermionpyscf

def pyscf_code_run(molecule_name,geometry,basis,method):
    from pyscf import gto, scf
    threshold =1e-12
    mol = gto.Mole()
    mol.verbose = 5
    mol.output = molecule_name+'.log'
    mol.atom = geometry
    mol.basis = basis

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

    one_body_integrals = moh1_qubit
    classical_output.one_body_integrals = one_body_integrals
    
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

    two_body_integrals = moh2_qubit
    classical_output.two_body_integrals = two_body_integrals
    code_str = pyscf_code_print(molecule_name,geometry,basis,method)
    classical_output.calculations_ran = True
    code_str = pyscf_code_print(molecule_name,geometry,basis,method)
    return code_str, classical_output
    
def pyscf_code_print(molecule_name: str,geometry: str ,basis: str,method: str):
    code_string = '''from pyscf import gto
    mol = gto.Mole()
    mol.verbose = 5
    mol.output = '''+molecule_name+'''.log
    mol.atom = '''+str(geometry)+'''
    mol.basis = '''+basis

    code_string=code_string+'''\n classical_output = classical_calc_output(molecule_name, geometry, basis, library)'''
    
    if method == 'RHF':
        code_string=code_string+'''scf_setup = scf.RHF(mol)'''
    elif method=='UHF':
        code_string=code_string+'''scf_setup = scf.UHF(mol)'''
    elif method=='ROHF':
        code_string=code_string+'''scf_setup = scf.ROHF(mol)'''
    else:
        code_string=code_string+'''scf_setup = scf.RHF(mol)'''
    
    code_string=code_string+'''
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
    driver = PySCFDriver(atom=geometry, basis='sto3g',hf_method=HFMethodType.RHF,)
    qmolecule = driver.run()
    classical_output = classical_calc_output(molecule_name,geometry,basis,library='qiskit')
    classical_output.one_body_integrals = qmolecule.one_body_integrals
    classical_output.two_body_integrals = qmolecule.two_body_integrals
    classical_output.calculations_ran = True
    code_str = qiskit_classical_code_print(molecule_name,geometry,basis,method)
    return code_str, classical_output
    
def qiskit_classical_code_print(molecule_name,geometry,basis,method):
    pyscfdriver_code_string = 'PySCFDriver(atom='+molecule_name+', basis='+basis+',hf_method=HFMethodType.'+method+')'
    code_string = '''import numpy as np
    from qiskit.chemistry.drivers import PySCFDriver, HFMethodType
    driver ='''+pyscfdriver_code_string+'''
    qmolecule = driver.run()
    classical_output = classical_calc_output(molecule_name,geometry,basis,library)
    classical_output.one_body_integrals = qmolecule.one_body_integrals
    classical_output.two_body_integrals = qmolecule.two_body_integrals
    '''
    return code_string

def openfermion_classical_code_run(molecule_name,geometry,basis,method):   
    if isinstance(geometry,str):
        geometry=get_openfermion_geometry(geometry)
    
    charge = 0
    multiplicity = 1
    of_molecule = openfermionpyscf.generate_molecular_hamiltonian(
            geometry, 'sto-3g', multiplicity)
    classical_output = classical_calc_output(molecule_name,geometry,basis,library='qiskit')
    classical_output.calculations_ran = True
    classical_output.one_body_integrals = of_molecule.one_body_tensor
    classical_output.two_body_integrals = of_molecule.two_body_tensor
    code_str = openfermion_classical_code_print(molecule_name,geometry,basis,method)
    return code_str, classical_output

def get_openfermion_geometry(geometry_str):
    geo_list = geometry_str.replace(';',' ').split()
    geometry = []
    for i in range(int(len(geo_list)/4)):
        atom = [geo_list[4*i]]
        coord = [float(geo_list[4*i+1]),float(geo_list[4*i+2]),float(geo_list[4*i+3])]
        atom.append(coord)
        geometry.append(atom)
    return geometry

def openfermion_classical_code_print(molecule_name,geometry,basis,method):
    code_string ='''import openfermionpyscf
    from qBraid_chem_app.classical_pipeline import get_openfermion_geometry,classical_calc_output'''
    if isinstance(geometry,str):
        code_string+='''get_openfermion_geometry(geometry)'''

    code_string+='''charge = 0
    multiplicity = 1
    of_molecule = openfermionpyscf.generate_molecular_hamiltonian('''+
            geometry+','+basis+','+ '''multiplicity)
    classical_output = classical_calc_output('''+molecule_name','+str(geometry)+','+basis','+'''library=openfermion)
    classical_output.calculations_ran = True
    classical_output.one_body_integrals = of_molecule.one_body_tensor
    classical_output.two_body_integrals = of_molecule.two_body_tensor'''
    return code_string

class classical_calc_output():
    def __init__(self,molecule_name: str, geometry: str, basis: str, library: str):
        self.molecule_name = molecule_name
        self.geometry = geometry
        self.basis = basis
        self.library = library
        self.calculations_ran = False
        self.one_body_integrals = None
        self.two_body_integrals = None
        self.num_particles = None
        self.pyscf_result_object = None
        self.qiskit_hamiltonian_object = None
        self.hf_energy = None
        self.code_str = None
