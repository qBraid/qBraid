# pylint: skip-file

from classical_pipeline import (
    pyscf_code_print,
    pyscf_code_run,
    qiskit_classical_code_print,
    qiskit_classical_code_run,
    classical_calc_output,
    openfermion_classical_code_run,
    openfermion_classical_code_print,
)
from quantum_pipeline import (
    qiskit_quantum_code_print,
    qiskit_quantum_code_run,
    openfermion_quantum_code_print,
    openfermion_quantum_code_run,
)
from run_setup import run_config_qiskit_run


class ChemAppResults:
    def __init__(self, classical_output, quantum_output):
        self.classical_output = classical_output
        self.quantum_output = quantum_output
        self.ground_state_energy = None
        self.run_config = None


def classical_cal(
        molecule_name,
        geometry,
        library: str = "pyscf",
        basis="sto-3g",
        method="HF",
        print_code=False,
):
    """Classical calculation. More customization will be provided in the newer versions.

    Args:
        library (str): string specifying the library. Valid inputs: 'pyscf','qiskit', 'psi4',
            'Gaussian', 'openfermion4pyscf'
        molecule_name (str): name of the molecule
        geometry (str|list): geometry string specified according to pyscf/openfermion convention.
        basis (str): basis
        method (str): classical scf method
        print_code (bool): optional boolean, defaults to False

    Returns:
        classical_calc_output object which contains the data from classical calculations

    Raises:
        Exception('invalid library')

    """
    # Inputs for pyscf that we may want to include
    if library == "pyscf":
        if print_code:
            code_str, classical_output = pyscf_code_print(molecule_name, geometry, basis, method)
        else:
            code_str, classical_output = pyscf_code_run(molecule_name, geometry, basis, method)

    elif library == "qiskit":
        if print_code:
            code_str, classical_output = qiskit_classical_code_print(
                molecule_name, geometry, basis, method
            )
        else:
            code_str, classical_output = qiskit_classical_code_run(
                molecule_name, geometry, basis, method
            )

    elif library == "psi4":
        raise NotImplementedError

    elif library == "openfermionpyscf":
        if print_code:
            code_str, classical_output = openfermion_classical_code_print(
                molecule_name, geometry, basis, method
            )
        else:
            code_str, classical_output = openfermion_classical_code_run(
                molecule_name, geometry, basis, method
            )

    elif library == "gaussian":
        raise NotImplementedError

    else:
        raise Exception("invalid library")

    return code_str, classical_output


def quantum_calc(
        library: str,
        classical_output: classical_calc_output,
        mapping: str = "jordan_wigner",
        qubit_tapering=False,
        algorithm: str = "exact_diag",
        algo_config: dict = None,
        print_code: bool = False,
):
    """Quantum calculation. More customization will be provided in the newer versions.

    Args:
        library (str): string specifying the library. Valid inputs:'qiskit','openfermion'
        classical_output (cls): classical output
        mapping (str): valid inputs: 'jordan_wigner', 'bravyi_kitaev', 'parity'
        qubit_tapering (bool): for specifying if qubits are to be tapered. present only in qiskit
        algorithm (str): valid inputs: 'exact_diag', 'vqe', 'ipea'
        algo_config (dict):
            exact_diag_dict: {'num_of_evs': int}
            vqe_dict: {'optimizer': 'COBYLA'|'SPSA'|'SLSQP', 'var_form': 'EfficientSU2'|'UCCSD',
                'entanglement': 'full'|'linear', 'classical_algo_max_iter':10, 'initial_state':'HF'}
        print_code (bool): boolean, defaults to False

    Returns:
        classical_calc_output object which contains the data from classical calculations

    Raises:
        Exception('invalid library')

    """
    if algo_config is None:
        algo_config = {"num_of_evs": 2}  # default algo config

    # Inputs for pyscf that we may want to include
    if library == "qiskit":
        if print_code:
            code_str, quantum_output = qiskit_quantum_code_print(
                classical_output, mapping, qubit_tapering, algorithm, algo_config
            )
        else:
            code_str, quantum_output = qiskit_quantum_code_run(
                classical_output, mapping, qubit_tapering, algorithm, algo_config
            )
    elif library == "openfermion":
        if print_code:
            code_str, quantum_output = openfermion_quantum_code_print(
                classical_output, mapping, qubit_tapering, algorithm, algo_config
            )
        else:
            code_str, quantum_output = openfermion_quantum_code_run(
                classical_output, mapping, qubit_tapering, algorithm, algo_config
            )
    else:
        raise Exception("invalid library")

    return code_str, quantum_output


def run(
        library,
        quantum_calc_output,
        run_on_hardware=False,
        hardware_config=None,
        simulation_config=None,
):
    """Run method. More customization will be provided in the newer versions.

    Args:
        library (str): string specifying the library. Valid inputs:'qiskit','cirq'
        quantum_calc_output (cls): quantum calculation output
        run_on_hardware (bool): boolean specifying whether to run on hardware
        hardware_config (dict): TBD soon
        simulation_config (dict): {
            'Noisy': True|False,
            'simulator': 'qasm_simulator'|'statevecgtor_simulator',
            'device_name': 'vigo'|'montreal'|'melbourne'|'fakeqasm'
        }

    Returns:
        classical_calc_output object which contains the data from classical calculations.

    Raises:
        Exception('invalid library')

    """

    if library == "qiskit":
        run_config_qiskit_run(
            quantum_calc_output, run_on_hardware, hardware_config, simulation_config
        )

    elif library == "cirq":
        raise NotImplementedError

    else:
        raise Exception("invalide library")


if __name__ == "__main__":
    # Checking everything with default parameters
    # classical checks
    # classical_library='qiskit'
    # quantum_library='qiskit'
    # code_str,classical_output=classical_cal()
    # code_str,classical_output=classical_cal(classical_library)
    # print(classical_output.one_body_integrals)

    # classical_library = 'openfermionpyscf'
    # code_str,classical_output=classical_cal(classical_library)
    # #quantum checks
    # code_str,quantum_output = quantum_calc(quantum_library,classical_output)
    # # run configuration check
    # run_library = 'qiskit'
    # print(classical_output.one_body_integrals)

    # Custom configuration runs
    cl_lib = "qiskit"
    qtm_lib = "qiskit"
    test_molecule = "H2"
    test_geom = "H 0 0 0; H 0 0 .7414"
    test_basis = "sto-3g"
    test_mtd = "HF"
    code_string, cl_output = classical_cal(test_molecule, test_geom, cl_lib, test_basis, test_mtd)
    print(cl_output.num_particles)
    # Running quantum pipeline for VQE
    test_algorithm = "vqe"
    test_vqe_config = {
        "optimizer": "COBYLA",
        "var_form": "UCCSD",
        "entanglement": "linear",
        "classical_algo_max_iter": 10,
        "initial_state": "HF",
    }
    q_code_str, q_output = quantum_calc(
        qtm_lib, cl_output, algorithm=test_algorithm, algo_config=test_vqe_config
    )
    test_simulation_config = {
        "Noisy": True,
        "simulator": "qasm_simulator",
        "device_name": "vigo",
    }
    run(qtm_lib, q_output, simulation_config=test_simulation_config)


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
