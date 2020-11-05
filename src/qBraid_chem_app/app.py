# -*- coding: utf-8 -*-
# All rights reserved-2020©. 
from .classical_pipeline import (pyscf_code_print,pyscf_code_run,
                            qiskit_classical_code_print,qiskit_classical_code_run,
                            classical_calc_output,openfermion_classical_code_run,
                            openfermion_classical_code_print)
from .quantum_pipeline import (qiskit_quantum_code_print, qiskit_quantum_code_run,
                                openfermion_quantum_code_print, openfermion_quantum_code_run,
                                quantum_calc_output)
from .run_setup import (run_config_qiskit_run)
import numpy as np
import numpy
from pyscf import gto, ao2mo
from qiskit.chemistry.drivers import PySCFDriver, HFMethodType
from qiskit import QuantumCircuit, ClassicalRegister, QuantumRegister, execute
from qiskit.aqua.operators import Z2Symmetries
import numpy as np


from qBraid.conversions import qub_op_conversion, fer_op_conversion

class chem_app_results():
    def __init__(self,classical_output,quantum_output):
        self.classical_output = classical_output
        self.quantum_output = quantum_output
        self.ground_state_energy = None
        self.run_config = None
        
def classical_cal(molecule_name,
                  geometry,library:str='pyscf',basis = 'sto-3g',
                  method='HF', print_code=False):
    """
        Args:
            library (str): string specifying the library. Valid inputs: 'pyscf','qiskit',
                            'psi4', 'Gaussian', 'openfermion4pyscf'
            molecule_name (str): name of the molecule
            geometry (str|list): geometry string specified according to pyscf/openfermion
                                 convention.
            basis (str): 
            method: classical scf method

            More customization will be provided in the newer versions.

        Returns: classical_calc_output object which contains the data from classical
                calculations
        Raises: Exception('invalid library')

        """
    code_str = None
    classical_output = None
    # Inputs for pyscf that we may want to include
    if library=='pyscf':
        if print_code:
            code_str, classical_output = pyscf_code_print(molecule_name, geometry,basis,method)
        else:
            code_str, classical_output = pyscf_code_run(molecule_name, geometry,basis,method)
    elif library=='qiskit':
        if print_code:
            code_str,classical_output = qiskit_classical_code_print(molecule_name, 
                                                                    geometry,basis,method)
        else:
            code_str, classical_output = qiskit_classical_code_run(molecule_name,
                                                                   geometry,basis,method)
    elif library=='psi4':
        pass
    elif library=='openfermionpyscf':
        if print_code:
            code_str,classical_output = openfermion_classical_code_print(molecule_name, 
                                                                    geometry,basis,method)
        else:
            code_str, classical_output = openfermion_classical_code_run(molecule_name,
                                                                   geometry,basis,method)
    elif library=='gaussian':
        pass
    else:
        raise Exception('invalid library')
    return code_str,classical_output
    
def quantum_calc(library:str,classical_output:classical_calc_output,
                 mapping:str='jordan_wigner', 
                qubit_tapering=False,algorithm:str='exact_diag',  
                algo_config:dict={'num_of_evs':2},print_code:bool=False):
    """
        Args:
            library (str): string specifying the library. Valid inputs:'qiskit','openfermion'
            classical_calc_output (cls):
            mapping (str): valid inputs: 'jordan_wigner', 'bravyi_kitaev', 'parity'
            qubit_tapering (bool): for specifying if qubits are to be tapered. present
                                only in qiskit
            algorithm (str): valid inputs: 'exact_diag', 'vqe', 'ipea' 
            algo_config (dict): exact_diag_dict: {'num_of_evs': int}
                                vqe_dict: {'optimizer': 'COBYLA'|'SPSA'|'SLSQP',
                                            'var_form': 'EfficientSU2'|UCCSD
                                            'entanglement': 'full'|'linear'
                                            }
            print_code (bool): 

            More customization will be provided in the newer versions.

        Returns: classical_calc_output object which contains the data from classical
                calculations
        Raises: Exception('invalid library')

        """
    # Inputs for pyscf that we may want to include
    if library=='qiskit':
        if print_code:
            code_str,quantum_output = qiskit_quantum_code_print(classical_output, mapping, 
                qubit_tapering,algorithm,
                algo_config)
        else:
            code_str, quantum_output = qiskit_quantum_code_run(classical_output, mapping, 
                qubit_tapering,algorithm,algo_config)
    elif library=='openfermion':
        if print_code:
            code_str, quantum_output = openfermion_quantum_code_print(classical_output, mapping,
                            qubit_tapering,algorithm,algo_config)
        else:
            code_str, quantum_output = openfermion_quantum_code_run(classical_output, mapping,
                                                qubit_tapering,algorithm,algo_config)
    else:
        pass
    return code_str, quantum_output


def run(library, quantum_calc_output, run_on_hardware=False,
         hardware_cofig=None,simulation_config=None):
    """
        Args:
            library (str): string specifying the library. Valid inputs:'qiskit','cirq'
            quantum_calc_output (cls):  
            run_on_hardware (bool): 
            hardware_config (dict): TBD soon
            simulation_config (dict): {'Noisy': True|False,
                                            'simulator': 'qasm_simulator'|'statevecgtor_simulator'
                                            'device_name': 'vigo'|'montreal'|'melbourne'|'fakeqasm'}
            

            More customization will be provided in the newer versions.

        Returns: classical_calc_output object which contains the data from classical
                calculations
        Raises: Exception('invalid library')

        """
    
    if library=='qiskit':
        run_config_qiskit_run(quantum_calc_output, run_on_hardware, hardware_cofig,
                    simulation_config)
    elif library=='cirq':
        pass




if __name__ == "__main__":
    # Checking everything with default parameters
    # classical checks 
    classical_library='qiskit'
    quantum_library='qiskit'
    code_str,classical_output=classical_cal()
    code_str,classical_output=classical_cal(classical_library)
    print(classical_output.one_body_integrals)
    
    
    classical_library = 'openfermionpyscf'
    code_str,classical_output=classical_cal(classical_library)
    #quantum checks
    code_str,quantum_output = quantum_calc(quantum_library,classical_output)
    # run configuration check
    run_library = 'qiskit'
    print(classical_output.one_body_integrals)
    
    
    # # Custom configuration runs
    # classical_library='qiskit'
    # quantum_library='qiskit'
    # molecule = 'H2'
    # geometry = 'H 0 0 0; H 0 0 .7414'
    # basis = 'sto-3g'
    # method='HF'
    # code_str,classical_output=classical_cal(quantum_library,molecule,
    #                             geometry,basis,method)
    # # Running quantum pipeline for VQE
    # algorithm = 'vqe'
    # vqe_config = {'optimizer': 'COBYLA',
    #              'var_form': 'EfficientSU2',
    #              'entanglement': 'linear'}
    # q_code_str, q_output = quantum_calc(quantum_library,classical_output,
    #                                     algorithm=algorithm,algo_config=vqe_config)
    # simulation_config = {'Noisy': False,
    #                     'simulator': 'statevector_simulator',
    #                     'device_name': 'vigo'}
    # run(quantum_library,q_output, simulation_config=simulation_config)


#  Noisy VQE runs
    # classical_library='qiskit'
    # quantum_library='qiskit'
    # molecule = 'H2'
    # geometry = 'H 0 0 0; H 0 0 .7414'
    # basis = 'sto-3g'
    # method='HF'
    # code_str,classical_output=classical_cal(quantum_library,molecule,
    #                             geometry,basis,method)
    # # Running quantum pipeline for VQE
    # algorithm = 'vqe'
    # vqe_config = {'optimizer': 'COBYLA',
    #              'var_form': 'EfficientSU2',
    #              'entanglement': 'linear'}
    
    # q_code_str, q_output = quantum_calc(quantum_library,classical_output,
    #                                     algorithm=algorithm,algo_config=vqe_config)
    # simulation_config = {'Noisy': True,
    #                     'simulator': 'qasm_simulator',
    #                     'device_name': 'vigo'}
    # run(quantum_library,q_output, simulation_config=simulation_config)




