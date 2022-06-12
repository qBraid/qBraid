"""
Unit tests for the qbraid transpiler.

"""
import cirq
import numpy as np
import pytest
from braket.circuits import Circuit as BraketCircuit
from braket.circuits import Gate as BraketGate
from braket.circuits import Instruction as BraketInstruction
from cirq import Circuit as CirqCircuit
from qiskit import QuantumCircuit as QiskitCircuit
from qiskit import QuantumRegister as QiskitQuantumRegister
from qiskit.circuit.quantumregister import Qubit as QiskitQubit

from qbraid import QbraidError, circuit_wrapper
from qbraid.interface import convert_to_contiguous, to_unitary
from qbraid.interface.programs import bell_data, random_circuit, shared15_data
from qbraid.transpiler.cirq_braket.tests._gate_archive import braket_gates
from qbraid.transpiler.cirq_qiskit.tests._gate_archive import qiskit_gates
from qbraid.transpiler.cirq_utils.tests._gate_archive import cirq_gates, create_cirq_gate

TEST_15, UNITARY_15 = shared15_data()
TEST_BELL, UNITARY_BELL = bell_data()


def test_circuit_wrapper_error():
    """Test raising circuit wrapper error"""
    with pytest.raises(QbraidError):
        circuit_wrapper("Not a circuit")


def shared_gates_test_data(package):
    """Returns data ``TestSharedGates``."""
    circuit = TEST_15[package]()
    qbraid_circuit = circuit_wrapper(circuit)
    return qbraid_circuit


def bell_test_data(package):
    """Returns data ``TestSharedGates``."""
    circuit = TEST_BELL[package]()
    qbraid_circuit = circuit_wrapper(circuit)
    return qbraid_circuit


# Define circuits and unitaries
qbraid_braket_shared = shared_gates_test_data("braket")
qbraid_cirq_shared = shared_gates_test_data("cirq")
qbraid_qiskit_shared = shared_gates_test_data("qiskit")

qbraid_braket_bell = bell_test_data("braket")
qbraid_cirq_bell = bell_test_data("cirq")
qbraid_pennylane_bell = bell_test_data("pennylane")
qbraid_pyquil_bell = bell_test_data("pyquil")
qbraid_qiskit_bell = bell_test_data("qiskit")


data_test_15 = [
    (qbraid_braket_shared, "cirq"),
    (qbraid_braket_shared, "qiskit"),
    (qbraid_qiskit_shared, "braket"),
    (qbraid_qiskit_shared, "cirq"),
    (qbraid_cirq_shared, "braket"),
    (qbraid_cirq_shared, "qiskit"),
]

data_test_bell = [
    (qbraid_braket_bell, "cirq"),
    (qbraid_braket_bell, "qiskit"),
    (qbraid_braket_bell, "pennylane"),
    (qbraid_braket_bell, "pyquil"),
    (qbraid_qiskit_bell, "braket"),
    (qbraid_qiskit_bell, "cirq"),
    (qbraid_qiskit_bell, "pennylane"),
    (qbraid_qiskit_bell, "pyquil"),
    (qbraid_cirq_bell, "braket"),
    (qbraid_cirq_bell, "qiskit"),
    (qbraid_cirq_bell, "pennylane"),
    (qbraid_cirq_bell, "pyquil"),
    (qbraid_pennylane_bell, "braket"),
    (qbraid_pennylane_bell, "cirq"),
    (qbraid_pennylane_bell, "pyquil"),
    (qbraid_pennylane_bell, "qiskit"),
    (qbraid_pyquil_bell, "braket"),
    (qbraid_pyquil_bell, "cirq"),
    (qbraid_pyquil_bell, "pennylane"),
    (qbraid_pyquil_bell, "qiskit"),
]


@pytest.mark.parametrize("qbraid_circuit,target_package", data_test_15)
def test_15(qbraid_circuit, target_package):
    """Tests transpiling circuits composed of gate types that share explicit support across
    multiple qbraid tranpsiler supported packages (qiskit, cirq, braket).
    """
    transpiled_circuit = qbraid_circuit.transpile(target_package)
    transpiled_unitary = to_unitary(transpiled_circuit)
    cirq.testing.assert_allclose_up_to_global_phase(transpiled_unitary, UNITARY_15, atol=1e-7)
    # assert np.allclose(transpiled_unitary, target_unitary)


@pytest.mark.parametrize("qbraid_circuit,target_package", data_test_bell)
def test_bell(qbraid_circuit, target_package):
    """Tests transpiling bell circuits."""
    transpiled_circuit = qbraid_circuit.transpile(target_package)
    transpiled_unitary = to_unitary(transpiled_circuit)
    assert np.allclose(transpiled_unitary, UNITARY_BELL)


def nqubits_nparams(gate):
    if gate in ["H", "X", "Y", "Z", "S", "Sdg", "T", "Tdg", "I", "SX", "SXdg"]:
        return 1, 0
    elif gate in ["Phase", "RX", "RY", "RZ", "U1", "HPow", "XPow", "YPow", "ZPow"]:
        return 1, 1
    elif gate in ["R", "U2"]:
        return 1, 2
    elif gate in ["U", "U3"]:
        return 1, 3
    elif gate in ["CX", "CSX", "CH", "DCX", "Swap", "iSwap", "CY", "CZ"]:
        return 2, 0
    elif gate in ["RXX", "RXY", "RZX", "RYY", "CU1", "CRY", "RZZ", "CRZ", "CRX", "pSwap", "CPhase"]:
        return 2, 1
    elif gate in ["CCX", "RCCX"]:
        return 3, 0
    elif gate in ["CCZ"]:
        return 3, 1
    else:
        raise ValueError(f"Gate {gate} not accounted for")


def assign_params(init_gate1, init_gate2, nparams):
    params = np.random.random_sample(nparams) * np.pi
    return init_gate1(*params), init_gate2(*params)


def assign_params_cirq(gate_str, init_gate2, nparams):
    params = np.random.random_sample(nparams) * np.pi
    cirq_data = {"type": gate_str, "params": params, "matrix": None}
    new_cirq_gate = create_cirq_gate(cirq_data)
    return new_cirq_gate, init_gate2(*params)


def braket_gate_test_circuit(test_gate, nqubits, only_test_gate=False):
    qubits = [i for i in range(nqubits)] if nqubits > 1 else 0

    gates_qubits = [
        (BraketGate.H(), 0),
        (BraketGate.H(), 1),
        (BraketGate.H(), 2),
        (test_gate, qubits),
        (BraketGate.CNot(), [0, 1]),
        (BraketGate.Ry(np.pi), 2),
    ]

    if only_test_gate:
        gates_qubits = [(test_gate, qubits)]

    circuit = BraketCircuit([BraketInstruction(*gate_qubit) for gate_qubit in gates_qubits])

    # print()
    # print(circuit)

    unitary = to_unitary(circuit)
    qbraid_circuit = circuit_wrapper(circuit)

    return unitary, qbraid_circuit


def qiskit_gate_test_circuit(test_gate, nqubits):
    qreg = QiskitQuantumRegister(3, name="q")
    circuit = QiskitCircuit(qreg)
    circuit.h([0, 1, 2])
    qubits = [QiskitQubit(qreg, i) for i in range(nqubits)]
    circuit.append(test_gate, qubits)
    circuit.cx(0, 1)
    circuit.ry(np.pi, 2)

    # print()
    # print(circuit)

    unitary = to_unitary(circuit)
    qbraid_circuit = circuit_wrapper(circuit)

    return unitary, qbraid_circuit


def cirq_gate_test_circuit(test_gate, nqubits):

    circuit = CirqCircuit()
    q2, q1, q0 = [cirq.LineQubit(i) for i in range(3)]
    # mapping = {q2: 0, q1: 1, q0: 2}

    if nqubits == 1:
        input_qubits = [q0]
    elif nqubits == 2:
        input_qubits = [q0, q1]
    else:
        input_qubits = [q0, q1, q2]

    cirq_gate_test_gates = [
        cirq.H(q0),
        cirq.H(q1),
        cirq.H(q2),
        test_gate(*input_qubits),
        cirq.ry(rads=np.pi)(q2),
        cirq.CNOT(q0, q1),
    ]

    for gate in cirq_gate_test_gates:
        circuit.append(gate)

    # print()
    # print(circuit)

    unitary = to_unitary(circuit)
    qbraid_circuit = circuit_wrapper(circuit)

    return unitary, qbraid_circuit


braket_gate_set = set(braket_gates.keys())
qiskit_gate_set = set(qiskit_gates.keys())
cirq_gate_set = set(cirq_gates.keys())

intersect_braket_qiskit = list(braket_gate_set.intersection(list(qiskit_gate_set)))
intersect_qiskit_cirq = list(qiskit_gate_set.intersection(list(cirq_gate_set)))
intersect_cirq_braket = list(cirq_gate_set.intersection(list(braket_gate_set)))

# skipped by old transpiler
intersect_braket_qiskit.remove("Unitary")
intersect_qiskit_cirq.remove("Unitary")
intersect_qiskit_cirq.remove("MEASURE")
intersect_cirq_braket.remove("Unitary")

# skipping with new transpiler
intersect_braket_qiskit.remove("RXX")
intersect_braket_qiskit.remove("RYY")


@pytest.mark.parametrize("gate_str", intersect_braket_qiskit)
def test_gate_intersect_braket_qiskit(gate_str):
    braket_init_gate = braket_gates[gate_str]
    qiskit_init_gate = qiskit_gates[gate_str]
    nqubits, nparams = nqubits_nparams(gate_str)
    qiskt_gate, braket_gate = assign_params(qiskit_init_gate, braket_init_gate, nparams)
    braket_u, qbraid_braket_circ = braket_gate_test_circuit(braket_gate, nqubits)
    qiskit_u, qbraid_qiskit_circ = qiskit_gate_test_circuit(qiskt_gate, nqubits)
    cirq.testing.assert_allclose_up_to_global_phase(braket_u, qiskit_u, atol=1e-7)
    # assert np.allclose(braket_u, qiskit_u)
    braket_circuit_transpile = qbraid_qiskit_circ.transpile("braket")
    qiskit_circuit_transpile = qbraid_braket_circ.transpile("qiskit")
    braket_transpile_u = to_unitary(braket_circuit_transpile)
    qiskit_transpile_u = to_unitary(qiskit_circuit_transpile)
    cirq.testing.assert_allclose_up_to_global_phase(braket_u, braket_transpile_u, atol=1e-7)
    cirq.testing.assert_allclose_up_to_global_phase(qiskit_u, qiskit_transpile_u, atol=1e-7)
    # assert np.allclose(braket_u, braket_transpile_u)
    # assert np.allclose(qiskit_u, qiskit_transpile_u)


@pytest.mark.parametrize("gate_str", intersect_qiskit_cirq)
def test_gate_intersect_qiskit_cirq(gate_str):
    qiskit_init_gate = qiskit_gates[gate_str]
    nqubits, nparams = nqubits_nparams(gate_str)
    cirq_gate, qiskit_gate = assign_params_cirq(gate_str, qiskit_init_gate, nparams)
    cirq_u, qbraid_cirq_circ = cirq_gate_test_circuit(cirq_gate, nqubits)
    qiskit_u, qbraid_qiskit_circ = qiskit_gate_test_circuit(qiskit_gate, nqubits)
    cirq.testing.assert_allclose_up_to_global_phase(cirq_u, qiskit_u, atol=1e-7)
    # assert np.allclose(cirq_u, qiskit_u)
    qiskit_circuit_transpile = qbraid_cirq_circ.transpile("qiskit")
    cirq_circuit_transpile = qbraid_qiskit_circ.transpile("cirq")
    qiskit_transpile_u = to_unitary(qiskit_circuit_transpile)
    cirq_transpile_u = to_unitary(cirq_circuit_transpile)
    cirq.testing.assert_allclose_up_to_global_phase(cirq_u, cirq_transpile_u, atol=1e-7)
    cirq.testing.assert_allclose_up_to_global_phase(qiskit_u, qiskit_transpile_u, atol=1e-7)
    # assert np.allclose(cirq_u, cirq_transpile_u)
    # assert np.allclose(qiskit_u, qiskit_transpile_u)


@pytest.mark.parametrize("gate_str", intersect_cirq_braket)
def test_gate_intersect_braket_cirq(gate_str):
    braket_init_gate = braket_gates[gate_str]
    nqubits, nparams = nqubits_nparams(gate_str)
    cirq_gate, braket_gate = assign_params_cirq(gate_str, braket_init_gate, nparams)
    cirq_u, qbraid_cirq_circ = cirq_gate_test_circuit(cirq_gate, nqubits)
    braket_u, qbraid_braket_circ = braket_gate_test_circuit(braket_gate, nqubits)
    cirq.testing.assert_allclose_up_to_global_phase(cirq_u, braket_u, atol=1e-7)
    # assert np.allclose(cirq_u, braket_u)
    braket_circuit_transpile = qbraid_cirq_circ.transpile("braket")
    cirq_circuit_transpile = qbraid_braket_circ.transpile("cirq")
    braket_transpile_u = to_unitary(braket_circuit_transpile)
    cirq_transpile_u = to_unitary(cirq_circuit_transpile)
    cirq.testing.assert_allclose_up_to_global_phase(cirq_u, cirq_transpile_u, atol=1e-7)
    cirq.testing.assert_allclose_up_to_global_phase(braket_u, braket_transpile_u, atol=1e-7)
    # assert np.allclose(cirq_u, cirq_transpile_u)
    # assert np.allclose(braket_u, braket_transpile_u)


yes_braket_no_qiskit = list(set(braket_gates).difference(qiskit_gates))
yes_qiskit_no_braket = list(set(qiskit_gates).difference(braket_gates))
yes_braket_no_cirq = list(set(braket_gates).difference(cirq_gates))
yes_cirq_no_braket = list(set(cirq_gates).difference(braket_gates))
yes_cirq_no_qiskit = list(set(cirq_gates).difference(qiskit_gates))
yes_qiskit_no_cirq = list(set(qiskit_gates).difference(cirq_gates))

yes_qiskit_no_braket.remove("MEASURE")
yes_qiskit_no_braket.remove("RC3X")
yes_qiskit_no_cirq.remove("RC3X")
yes_cirq_no_braket.remove("MEASURE")


@pytest.mark.parametrize("gate_str", yes_braket_no_qiskit)
def test_yes_braket_no_qiskit(gate_str):
    braket_init_gate = braket_gates[gate_str]
    nqubits, nparams = nqubits_nparams(gate_str)
    params = np.random.random_sample(nparams) * np.pi
    braket_gate = braket_init_gate(*params)
    braket_u, qbraid_braket_circ = braket_gate_test_circuit(braket_gate, nqubits)
    qiskit_circuit = qbraid_braket_circ.transpile("qiskit")
    qiskit_u = to_unitary(qiskit_circuit)
    cirq.testing.assert_allclose_up_to_global_phase(braket_u, qiskit_u, atol=1e-7)
    # assert np.allclose(braket_u, qiskit_u)


# @pytest.mark.skip(reason="conversion error gate not supported")
# @pytest.mark.parametrize("gate_str", yes_qiskit_no_braket)
# def test_yes_qiskit_no_braket(gate_str):
#     qiskit_init_gate = qiskit_gates[gate_str]
#     nqubits, nparams = nqubits_nparams(gate_str)
#     params = np.random.random_sample(nparams) * np.pi
#     qiskit_gate = qiskit_init_gate(*params)
#     qiskit_u, qbraid_qiskit_circ = qiskit_gate_test_circuit(qiskit_gate, nqubits)
#     braket_circuit = qbraid_qiskit_circ.transpile("braket")
#     braket_u = to_unitary(braket_circuit)
#     cirq.testing.assert_allclose_up_to_global_phase(qiskit_u, braket_u, atol=1e-7)
#     # assert np.allclose(qiskit_u, braket_u)


# @pytest.mark.skip(reason="conversion error gate not supported")
# @pytest.mark.parametrize("gate_str", yes_qiskit_no_cirq)
# def test_yes_qiskit_no_cirq(gate_str):
#     qiskit_init_gate = qiskit_gates[gate_str]
#     nqubits, nparams = nqubits_nparams(gate_str)
#     params = np.random.random_sample(nparams) * np.pi
#     qiskit_gate = qiskit_init_gate(*params)
#     qiskit_u, qbraid_qiskit_circ = qiskit_gate_test_circuit(qiskit_gate, nqubits)
#     cirq_circuit = qbraid_qiskit_circ.transpile("cirq")
#     cirq_u = to_unitary(cirq_circuit)
#     cirq.testing.assert_allclose_up_to_global_phase(qiskit_u, cirq_u, atol=1e-7)
#     # assert np.allclose(qiskit_u, cirq_u)


@pytest.mark.parametrize("gate_str", yes_braket_no_cirq)
def test_yes_braket_no_cirq(gate_str):
    braket_init_gate = braket_gates[gate_str]
    nqubits, nparams = nqubits_nparams(gate_str)
    params = np.random.random_sample(nparams) * np.pi
    braket_gate = braket_init_gate(*params)
    braket_u, qbraid_braket_circ = braket_gate_test_circuit(braket_gate, nqubits)
    cirq_circuit = qbraid_braket_circ.transpile("cirq")
    cirq_u = to_unitary(cirq_circuit)
    cirq.testing.assert_allclose_up_to_global_phase(braket_u, cirq_u, atol=1e-7)
    # assert np.allclose(braket_u, cirq_u)


@pytest.mark.parametrize("gate_str", yes_cirq_no_qiskit)
def test_yes_cirq_no_qiskit(gate_str):
    cirq_init_gate = cirq_gates[gate_str]
    nqubits, nparams = nqubits_nparams(gate_str)
    exp = np.random.random()
    cirq_gate = cirq_init_gate(exponent=exp)
    cirq_u, qbraid_cirq_circ = cirq_gate_test_circuit(cirq_gate, nqubits)
    qiskit_circuit = qbraid_cirq_circ.transpile("qiskit")
    qiskit_u = to_unitary(qiskit_circuit)
    cirq.testing.assert_allclose_up_to_global_phase(cirq_u, qiskit_u, atol=1e-7)
    # assert np.allclose(cirq_u, qiskit_u)


@pytest.mark.parametrize("gate_str", yes_cirq_no_braket)
def test_yes_cirq_no_braket(gate_str):
    cirq_init_gate = cirq_gates[gate_str]
    nqubits, nparams = nqubits_nparams(gate_str)
    if gate_str == "U3":
        params = np.random.random_sample(nparams)
        cirq_gate = cirq_init_gate(*params)
    else:
        exp = np.random.random()
        cirq_gate = cirq_init_gate(exponent=exp)
    cirq_u, qbraid_cirq_circ = cirq_gate_test_circuit(cirq_gate, nqubits)
    braket_circuit = qbraid_cirq_circ.transpile("braket")
    braket_u = to_unitary(braket_circuit)
    cirq.testing.assert_allclose_up_to_global_phase(cirq_u, braket_u, atol=1e-7)
    # assert np.allclose(cirq_u, braket_u)


def test_braket_transpile_ccnot():
    braket_circuit = BraketCircuit()
    braket_circuit.ccnot(2, 0, 1)
    braket_circuit.ccnot(3, 1, 0)
    qbraid_braket = circuit_wrapper(braket_circuit)
    qiskit_circuit = qbraid_braket.transpile("qiskit")
    braket_ccnot_unitary = to_unitary(braket_circuit)
    qiskit_ccnot_unitary = to_unitary(qiskit_circuit)
    cirq.testing.assert_allclose_up_to_global_phase(
        braket_ccnot_unitary, qiskit_ccnot_unitary, atol=1e-7
    )
    # assert np.allclose(braket_ccnot_unitary, qiskit_ccnot_unitary)


# @pytest.mark.skip(reason="conversion error gate not supported")
# def test_braket_transpile_unitary():
#     matrix = braket_gates["CCX"]().to_matrix()
#     braket_gate = braket_gates["Unitary"](matrix)
#     braket_u, qbraid_braket_circ = braket_gate_test_circuit(braket_gate, 3, only_test_gate=True)
#     qiskit_circuit = qbraid_braket_circ.transpile("qiskit")
#     qiskit_u = to_unitary(qiskit_circuit)
#     cirq.testing.assert_allclose_up_to_global_phase(braket_u, qiskit_u, atol=1e-7)
#     # assert np.allclose(braket_u, qiskit_u)


# @pytest.mark.skip(reason="lots of different errors")
# @pytest.mark.parametrize("num_qubits", [1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
# def test_1000_random_circuits(num_qubits):
#     for _ in range(10):
#         packages = ["braket", "qiskit", "cirq"]
#         i, j = np.random.randint(0, high=3), np.random.randint(0, high=2)
#         origin = packages[i]
#         del packages[i]
#         target = packages[j]
#         rand_circuit = random_circuit(origin, num_qubits=num_qubits)
#         origin_circuit = convert_to_contiguous(rand_circuit)
#         origin_unitary = to_unitary(origin_circuit)
#         target_circuit = circuit_wrapper(origin_circuit).transpile(target)
#         target_unitary = to_unitary(target_circuit)
#         if not cirq.testing.assert_allclose_up_to_global_phase(
#             origin_unitary, target_unitary, atol=1e-7
#         ):
#             # if not np.allclose(origin_unitary, target_unitary):
#             print()
#             print(f"failed {origin} --> {target}")
#             print()
#             print(origin)
#             print(origin_circuit)
#             print()
#             print(target)
#             print(target_circuit)
#             assert False
#     assert True


def test_non_contiguous_qubits_braket():
    braket_circuit = BraketCircuit()
    braket_circuit.h(0)
    braket_circuit.cnot(0, 2)
    braket_circuit.cnot(2, 4)
    test_circuit = convert_to_contiguous(braket_circuit)
    qbraid_wrapper = circuit_wrapper(test_circuit)
    cirq_circuit = qbraid_wrapper.transpile("cirq")
    qiskit_circuit = qbraid_wrapper.transpile("qiskit")
    braket_unitary = to_unitary(test_circuit)
    cirq_unitary = to_unitary(cirq_circuit)
    qiskit_unitary = to_unitary(qiskit_circuit)
    cirq.testing.assert_allclose_up_to_global_phase(braket_unitary, cirq_unitary, atol=1e-7)
    cirq.testing.assert_allclose_up_to_global_phase(qiskit_unitary, braket_unitary, atol=1e-7)
    # assert np.allclose(braket_unitary, cirq_unitary)
    # assert np.allclose(qiskit_unitary, braket_unitary)


def test_non_contiguous_qubits_cirq():
    cirq_circuit = CirqCircuit()
    q0 = cirq.LineQubit(4)
    q2 = cirq.LineQubit(2)
    q4 = cirq.LineQubit(0)
    cirq_circuit.append(cirq.H(q0))
    cirq_circuit.append(cirq.CNOT(q0, q2))
    cirq_circuit.append(cirq.CNOT(q2, q4))
    test_circuit = convert_to_contiguous(cirq_circuit)
    qbraid_wrapper = circuit_wrapper(test_circuit)
    qiskit_circuit = qbraid_wrapper.transpile("qiskit")
    braket_circuit = qbraid_wrapper.transpile("braket")
    cirq_unitary = to_unitary(test_circuit)
    qiskit_unitary = to_unitary(qiskit_circuit)
    braket_unitary = to_unitary(braket_circuit)
    cirq.testing.assert_allclose_up_to_global_phase(cirq_unitary, qiskit_unitary, atol=1e-7)
    cirq.testing.assert_allclose_up_to_global_phase(braket_unitary, cirq_unitary, atol=1e-7)
    # assert np.allclose(cirq_unitary, qiskit_unitary)
    # assert np.allclose(braket_unitary, cirq_unitary)


# @pytest.mark.skip(reason="assertion error")
# def test_non_contiguous_qubits_qiskit():
#     qiskit_circuit = QiskitCircuit(5)
#     qiskit_circuit.h(0)
#     qiskit_circuit.cx(0, 2)
#     qiskit_circuit.cx(2, 4)
#     qbraid_wrapper = circuit_wrapper(qiskit_circuit)
#     braket_circuit = qbraid_wrapper.transpile("braket")
#     cirq_circuit = qbraid_wrapper.transpile("cirq")
#     qiskit_unitary = to_unitary(qiskit_circuit)
#     braket_unitary = to_unitary(braket_circuit, ensure_contiguous=True)
#     cirq_unitary = to_unitary(cirq_circuit, ensure_contiguous=True)
#     cirq.testing.assert_allclose_up_to_global_phase(qiskit_unitary, braket_unitary, atol=1e-7)
#     cirq.testing.assert_allclose_up_to_global_phase(cirq_unitary, qiskit_unitary, atol=1e-7)
#     # assert np.allclose(qiskit_unitary, braket_unitary)
#     # assert np.allclose(cirq_unitary, qiskit_unitary)
