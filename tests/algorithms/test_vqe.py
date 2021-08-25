# from qiskit.aqua.algorithms import VQE, NumPyEigensolver

# from qbraid.algorithms import VQE
# from qbraid.algorithms.optimizers import SLSQP

# import matplotlib.pyplot as plt
# import numpy as np
# from qiskit.chemistry.components.variational_forms import UCCSD
# from qiskit.chemistry.components.initial_states import HartreeFock
# from qiskit.circuit.library import EfficientSU2
# from qiskit.aqua.components.optimizers import COBYLA, SPSA, SLSQP
# from qiskit.aqua.operators import Z2Symmetries
# from qiskit import IBMQ, BasicAer, Aer
# from qiskit.chemistry.drivers import PySCFDriver, UnitsType
# from qiskit.chemistry import FermionicOperator
# from qiskit.aqua import QuantumInstance
# from qiskit.ignis.mitigation.measurement import CompleteMeasFitter
# from qiskit.providers.aer.noise import NoiseModel


# def get_qubit_op(dist):
#     driver = PySCFDriver(atom="Li .0 .0 .0; H .0 .0 " + str(dist), unit=UnitsType.ANGSTROM,
#                          charge=0, spin=0, basis='sto3g')
#     molecule = driver.run()
#     freeze_list = [0]
#     remove_list = [-3, -2]
#     repulsion_energy = molecule.nuclear_repulsion_energy
#     num_particles = molecule.num_alpha + molecule.num_beta
#     num_spin_orbitals = molecule.num_orbitals * 2
#     remove_list = [x % molecule.num_orbitals for x in remove_list]
#     freeze_list = [x % molecule.num_orbitals for x in freeze_list]
#     remove_list = [x - len(freeze_list) for x in remove_list]
#     remove_list += [x + molecule.num_orbitals - len(freeze_list)  for x in remove_list]
#     freeze_list += [x + molecule.num_orbitals for x in freeze_list]
#     ferOp = FermionicOperator(h1=molecule.one_body_integrals, h2=molecule.two_body_integrals)
#     ferOp, energy_shift = ferOp.fermion_mode_freezing(freeze_list)
#     num_spin_orbitals -= len(freeze_list)
#     num_particles -= len(freeze_list)
#     ferOp = ferOp.fermion_mode_elimination(remove_list)
#     num_spin_orbitals -= len(remove_list)
#     qubitOp = ferOp.mapping(map_type='parity', threshold=0.00000001)
#     qubitOp = Z2Symmetries.two_qubit_reduction(qubitOp, num_particles)
#     shift = energy_shift + repulsion_energy
#     return qubitOp, num_particles, num_spin_orbitals, shift

# backend = BasicAer.get_backend("statevector_simulator")
# distances = [0.75] # np.arange(0.5, 4.0, 0.1)
# exact_energies = []
# vqe_energies = []
# optimizer = SLSQP(maxiter=5)
# for dist in distances:
#     qubitOp, num_particles, num_spin_orbitals, shift = get_qubit_op(dist)
#     result = NumPyEigensolver(qubitOp).run()
#     exact_energies.append(np.real(result.eigenvalues) + shift)
#     initial_state = HartreeFock(
#         num_spin_orbitals,
#         num_particles,
#         qubit_mapping='parity'
#     )
#     var_form = UCCSD(
#         num_orbitals=num_spin_orbitals,
#         num_particles=num_particles,
#         initial_state=initial_state,
#         qubit_mapping='parity'
#     )
#     vqe = VQE(qubitOp, var_form, optimizer)
#     vqe_result = np.real(vqe.run(backend)['eigenvalue'] + shift)
#     vqe_energies.append(vqe_result)
#     print("Interatomic Distance:", np.round(dist, 2), "VQE Result:", vqe_result,
#     "Exact Energy:", exact_energies[-1])


# print("All energies have been calculated")

from qiskit_nature.drivers import PySCFDriver, UnitsType
from qiskit_nature.problems.second_quantization.electronic import ElectronicStructureProblem

# Use PySCF, a classical computational chemistry software
# package, to compute the one-body and two-body integrals in
# electronic-orbital basis, necessary to form the Fermionic operator
driver = PySCFDriver(atom="H .0 .0 .0; H .0 .0 0.735", unit=UnitsType.ANGSTROM, basis="sto3g")
problem = ElectronicStructureProblem(driver)

# generate the second-quantized operators
second_q_ops = problem.second_q_ops()
main_op = second_q_ops[0]

num_particles = (
    problem.molecule_data_transformed.num_alpha,
    problem.molecule_data_transformed.num_beta,
)

num_spin_orbitals = 2 * problem.molecule_data.num_molecular_orbitals

# setup the classical optimizer for VQE
from qiskit.algorithms.optimizers import L_BFGS_B

optimizer = L_BFGS_B()

from qiskit_nature.converters.second_quantization import QubitConverter
# setup the mapper and qubit converter
from qiskit_nature.mappers.second_quantization import ParityMapper

mapper = ParityMapper()
converter = QubitConverter(mapper=mapper, two_qubit_reduction=True)

# map to qubit operators
qubit_op = converter.convert(main_op, num_particles=num_particles)

# setup the initial state for the ansatz
from qiskit_nature.circuit.library import HartreeFock

init_state = HartreeFock(num_spin_orbitals, num_particles, converter)

# setup the ansatz for VQE
from qiskit.circuit.library import TwoLocal

ansatz = TwoLocal(num_spin_orbitals, ["ry", "rz"], "cz")

# add the initial state
ansatz.compose(init_state, front=True)

# set the backend for the quantum computation
from qiskit import Aer

backend = Aer.get_backend("aer_simulator_statevector")

# setup and run VQE
from qbraid.algorithms import VQE

algorithm = VQE(ansatz, optimizer=optimizer, quantum_instance=backend)

result = algorithm.compute_minimum_eigenvalue(qubit_op)
print(result.eigenvalue.real)

electronic_structure_result = problem.interpret(result)
print(electronic_structure_result)
