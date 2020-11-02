from classical_pipeline import classical_calc_output
from qiskit.chemistry.drivers import PySCFDriver, HFMethodType
from qiskit import QuantumCircuit, ClassicalRegister, QuantumRegister, execute
from qiskit.aqua.operators import Z2Symmetries

from qiskit.aqua.components.optimizers import COBYLA, SPSA, SLSQP
from qiskit.aqua.algorithms import VQE, NumPyEigensolver
from qiskit.circuit.library import EfficientSU2
from qiskit.chemistry.components.variational_forms import UCCSD
from qiskit.chemistry import FermionicOperator

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
    if algo=='Exact_diag':
        from qiskit.aqua.algorithms import NumPyEigensolver as EE
        k = algo_config['num_of_evs']
        result = EE(qiskit_qub_op,k).run()
        # lines, result = operator.process_algorithm_result(result)
        energies = result['eigenvalues']
        output.qubit_op_evs = energies
    elif algo=='VQE':
        if algo_config['optimizer']=='SPSA':
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
        output.vqe_qiskit_obj = vqe
    return code_str, output

def qiskit_quantum_code_print(classical_output: classical_calc_output, mapping='jordan_wigner',
                            qubit_tapering=False, algo='VQE', algo_config=None):
    pass

def openfermion_quantum_code_run(classical_output: classical_calc_output, mapping='jordan_wigner',
                            qubit_tapering=False,algo='VQE', algo_config=None):
    from openfermion.hamiltonians import MolecularData
    from openfermion.transforms import (get_fermion_operator,
                                    get_sparse_operator, jordan_wigner,
                                    bravyi_kitaev, parity_code, bravyi_kitaev_fast)
    from openfermion.utils import get_ground_state

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
    code_str = openfermion_quantum_code_print(classical_output, mapping,
                            qubit_tapering)
    return code_str, output
                
def openfermion_quantum_code_print(classical_output: classical_calc_output, mapping='jordan_wigner',
                            qubit_tapering=False,algo='VQE', algo_config=None):
    pass


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
