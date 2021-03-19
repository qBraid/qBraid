from classical_pipeline import classical_calc_output
from qiskit.chemistry.drivers import PySCFDriver, HFMethodType
from qiskit import QuantumCircuit, ClassicalRegister, QuantumRegister, execute
from qiskit.aqua.operators import Z2Symmetries
from qiskit.chemistry.components.initial_states import HartreeFock

from qiskit.aqua.components.optimizers import COBYLA, SPSA, SLSQP
from qiskit.aqua.algorithms import VQE, NumPyEigensolver
from qiskit.circuit.library import EfficientSU2
from qiskit.chemistry.components.variational_forms import UCCSD
from qiskit.chemistry import FermionicOperator

from openfermion.hamiltonians import MolecularData
from openfermion.transforms import (get_fermion_operator,
                                get_sparse_operator, jordan_wigner,
                                bravyi_kitaev, parity_code, bravyi_kitaev_fast)
from openfermion.utils import get_ground_state
from openfermion.ops import FermionOperator, InteractionOperator

history = {'eval_count': [], 'parameters': [], 'mean': [], 'std': []}
def store_intermediate_result(eval_count, parameters, mean, std):
    history['eval_count'].append(eval_count)
    history['parameters'].append(parameters)
    history['mean'].append(mean)
    history['std'].append(std)
    print("Energy value", mean)

def qiskit_quantum_code_run(classical_output: classical_calc_output, mapping='jordan_wigner',
                            qubit_tapering=False, algo='VQE', algo_config=None):
    if not classical_output.calculations_ran:
        raise Exception('Run Classical calculations')
    one_b = classical_output.one_body_integrals
    two_b = classical_output.two_body_integrals
    fer_op = FermionicOperator(h1=one_b, h2=two_b)
    num_particles=classical_output.num_particles
    # transform the fermionic operator to qubit operator
    if mapping=='jordan_wigner':
        qubit_op = fer_op.mapping('jordan_wigner')
    elif mapping=='bravyi_kitaev':
        qubit_op = fer_op.mapping('bravyi_kitaev')
    elif mapping=='parity':
        qubit_op = fer_op.mapping('parity')        
    
    if qubit_tapering:
        qubit_op = Z2Symmetries.two_qubit_reduction(qubitOp, num_particles)
    
    output = quantum_calc_output(classical_output.molecule_name,
                                 classical_output.geometry,
                                  classical_output.basis,library='qiskit')
    output.fermionic_operator = fer_op
    output.qubit_operator = qubit_op
    code_str = qiskit_quantum_code_print(classical_output, mapping,
                            qubit_tapering)
    if algo=='exact_diag':
        output.algo_name=algo
        k = algo_config['num_of_evs']
        energies = qiskit_exact_diag(qubit_op,k)
        output.qubit_op_evs = energies
    elif algo=='vqe':
        output.algo_name=algo
        vqe_obj = qiskit_vqe(qubit_op,algo_config,mapping,num_particles)
        output.vqe_qiskit_obj = vqe_obj
    return code_str, output

def qiskit_exact_diag(qubit_op,k):
    from qiskit.aqua.algorithms import NumPyEigensolver as EE
    result = EE(qubit_op,k).run()
    energies = result['eigenvalues']
    return energies

def qiskit_vqe(qubit_op,algo_config,mapping='parity',particle_num=None):
    if algo_config['optimizer']=='SPSA':
        optimizer = SPSA(maxiter=algo_config['classical_algo_max_iter'])
    elif algo_config['optimizer']=='COBYLA':
        optimizer = COBYLA(maxiter=algo_config['classical_algo_max_iter'])
    elif algo_config['optimizer']=='SLSQP':
        optimizer = SLSQP(maxiter=algo_config['classical_algo_max_iter'])

    if algo_config['var_form']=='EfficientSU2':
        if algo_config['entanglement']=='linear':
            var_form = EfficientSU2(qubit_op.num_qubits, entanglement="linear")
        elif algo_config['entanglement']=='full':
            var_form = EfficientSU2(qubit_op.num_qubits,entanglement='full')
    elif algo_config['var_form']=='UCCSD':
        if particle_num:
            init_state = HartreeFock(num_orbitals=4,
                        qubit_mapping=mapping,
                        num_particles=2)
            var_form = UCCSD(num_orbitals=qubit_op.num_qubits, num_particles=particle_num,
                 two_qubit_reduction=False, shallow_circuit_concat=False,
                 initial_state=init_state)
            
            
        else:
            raise('number of particles not provided for uccsd')
        pass
    vqe = VQE(qubit_op, var_form, optimizer=optimizer, callback=store_intermediate_result)
    return vqe


def qiskit_quantum_code_print(classical_output: classical_calc_output, mapping='jordan_wigner',
                            qubit_tapering=False, algo='VQE', algo_config=None):
    code_str = '''# The following code will not work without first
    # running the classical pipeline
    one_b = classical_output.one_body_integrals
    two_b = classical_output.two_body_integrals
    fer_op = FermionicOperator(h1=one_b, h2=two_b)
    '''
    if mapping=='jordan_wigner':
        code_str+='''qubit_op = fer_op.mapping('jordan_wigner')
        '''
    elif mapping=='bravyi_kitaev':
        code_str+='''qubit_op = fer_op.mapping('bravyi_kitaev')
        '''
    elif mapping=='parity':
        code_str+='''qubit_op = fer_op.mapping('parity')
        '''
    if qubit_tapering:
        code_str+='''qubit_op = Z2Symmetries.two_qubit_reduction(qubitOp, num_particles)'''
    if algo=='Exact_diag':
        code_str+='''from qiskit.aqua.algorithms import NumPyEigensolver as EE
        k = algo_config['num_of_evs']
        result = EE(qubit_op,k).run()
        # lines, result = operator.process_algorithm_result(result)
        energies = result['eigenvalues']
        output.qubit_op_evs = energies'''
    elif algo=='VQE':
        code_str+='''if algo_config['optimizer']=='SPSA':
            optimizer = SPSA(maxiter=algo_config['classical_algo_max_iter'])
        elif algo_config['optimizer']=='COBYLA':
            optimizer = COBYLA(maxiter=algo_config['classical_algo_max_iter'])
        elif algo_config['optimizer']=='SLSQP':
            optimizer = SLSQP(maxiter=algo_config['classical_algo_max_iter'])

        if algo_config['var_form']=='EfficientSU2':
            if algo_config['entanglement']=='linear':
                var_form = EfficientSU2(qubitOp.num_qubits, entanglement="linear")
            elif algo_config['entanglement']=='full':
                var_form = EfficientSU2(qubitOp.num_qubits,entanglement='full')
        elif algo_config['var_form']=='UCCSD':
            pass
        vqe = VQE(qubitOp, var_form, optimizer=optimizer, callback=store_intermediate_result)
        output.vqe_qiskit_obj = vqe'''
    return code_str
    

def openfermion_quantum_code_run(classical_output: classical_calc_output, mapping='jordan_wigner',
                            qubit_tapering=False,algo='VQE', algo_config=None):
    int_op = InteractionOperator(0, one_body_tensor=classical_output.one_body_integrals,
                                two_body_tensor=classical_output.two_body_integrals)
    fer_op = get_fermion_operator(int_op)
    if mapping=='jordan_wigner':
        qubit_op = jordan_wigner(fer_op)
    elif mapping=='bravyi-kitaev':
        qubit_op =  bravyi_kitaev(fer_op)
    elif mapping=='parity':
        qubit_op = parity_code(fer_op)
    
    output = quantum_calc_output(classical_output.molecule_name,
                                 classical_output.geometry,
                                  classical_output.basis,library='openfermion')
    output.fermionic_operator = fer_op
    output.qubit_operator = qubit_op

    if qubit_tapering:
        raise Exception('This method is currently not available in openfermion')
        
    
    if algo=='exact_diag':
        output.algo_name=algo
        from openfermion.utils import eigenspectrum
        k = algo_config['num_of_evs']
        energies = eigenspectrum(qubit_op)
        output.qubit_op_evs = energies

    elif algo=='vqe':
        output.algo_name=algo
        from qBraid.conversions import qub_op_conversion
        qiskit_qub_op = qub_op_conversion.convert(qubit_op)
        vqe_obj = qiskit_vqe(qiskit_qub_op,algo_config)
        output.vqe_qiskit_obj = vqe_obj

    code_str = openfermion_quantum_code_print(classical_output, mapping,
                            qubit_tapering)
    return code_str, output
                
def openfermion_quantum_code_print(classical_output: classical_calc_output, mapping='jordan_wigner',
                            qubit_tapering=False,algo='VQE', algo_config=None):
    code_str = '''from openfermion.hamiltonians import MolecularData
    from openfermion.transforms import (get_fermion_operator,
                                    get_sparse_operator, jordan_wigner,
                                    bravyi_kitaev, parity_code, bravyi_kitaev_fast)
    from openfermion.utils import get_ground_state
    int_op = InteractionOperator(0, one_body_tensor=classical_output.one_body_integrals,
                                two_body_tensor=classical_output.two_body_integrals)
    fer_op = get_fermion_operator(int_op)
    '''
    if mapping=='jordan_wigner':
       code_str+=''' qubit_op = jordan_wigner(fer_op)
       '''
    elif mapping=='bravyi-kitaev':
        code_str+='''qubit_op =  bravyi_kitaev(fer_op)
        '''
    elif mapping=='parity':
        code_str+='''qubit_op = parity_code(fer_op)
        '''
    
    code_str+='''output = quantum_calc_output(classical_output.molecule_name,
                                 classical_output.geometry,
                                  classical_output.basis,library='openfermion')
    output.fermionic_operator = fer_op
    output.qubit_operator = qubit_op
    '''
    return code_str

class quantum_calc_output():
    def __init__(self,classical_output:classical_calc_output, geometry, basis, library):
        self.classical_output = classical_output
        self.library = library
        self.mapping = None
        self.qubit_operator = None
        self.fermionic_operator = None
        self.quantum_circ = None
        self.algo_name = None
        self.vqe_config = None
        self.vqe_qiskit_obj = None
        self.qubit_op_evs = None
