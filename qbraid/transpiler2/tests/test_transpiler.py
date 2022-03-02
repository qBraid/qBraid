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

from qbraid import circuit_wrapper, convert_to_contiguous, random_circuit, to_unitary
from qbraid.transpiler2.cirq_braket.tests._gate_archive import braket_gates
from qbraid.transpiler2.cirq_utils.tests._gate_archive import cirq_gates, create_cirq_gate
from qbraid.transpiler2.cirq_qiskit.tests._gate_archive import qiskit_gates


def qiskit_shared_gates_circuit():
    """Returns qiskit `QuantumCircuit` for qBraid `TestSharedGates`."""

    circuit = QiskitCircuit(4)

    circuit.h([0, 1, 2, 3])
    circuit.x([0, 1])
    circuit.y(2)
    circuit.z(3)
    circuit.s(0)
    circuit.sdg(1)
    circuit.t(2)
    circuit.tdg(3)
    circuit.rx(np.pi / 4, 0)
    circuit.ry(np.pi / 2, 1)
    circuit.rz(3 * np.pi / 4, 2)
    circuit.p(np.pi / 8, 3)
    circuit.sx(0)
    circuit.sxdg(1)
    circuit.iswap(2, 3)
    circuit.swap([0, 1], [2, 3])
    circuit.cx(0, 1)
    circuit.cp(np.pi / 4, 2, 3)

    unitary = to_unitary(circuit)
    qbraid_circuit = circuit_wrapper(circuit)

    return qbraid_circuit, unitary


def cirq_shared_gates_circuit():
    """Returns cirq `Circuit` for qBraid `TestSharedGates`
    rev_qubits=True reverses ordering of qubits."""

    circuit = CirqCircuit()
    q3, q2, q1, q0 = [cirq.LineQubit(i) for i in range(4)]
    mapping = {q3: 0, q2: 1, q1: 2, q0: 3}

    cirq_shared_gates = [
        cirq.H(q0),
        cirq.H(q1),
        cirq.H(q2),
        cirq.H(q3),
        cirq.X(q0),
        cirq.X(q1),
        cirq.Y(q2),
        cirq.Z(q3),
        cirq.S(q0),
        cirq.ZPowGate(exponent=-0.5)(q1),
        cirq.T(q2),
        cirq.ZPowGate(exponent=-0.25)(q3),
        cirq.rx(rads=np.pi / 4)(q0),
        cirq.ry(rads=np.pi / 2)(q1),
        cirq.rz(rads=3 * np.pi / 4)(q2),
        cirq.ZPowGate(exponent=1 / 8)(q3),
        cirq.XPowGate(exponent=0.5)(q0),
        cirq.XPowGate(exponent=-0.5)(q1),
        cirq.ISWAP(q2, q3),
        cirq.SWAP(q0, q2),
        cirq.SWAP(q1, q3),
        cirq.CNOT(q0, q1),
        cirq.CZPowGate(exponent=0.25)(q2, q3),
    ]

    for gate in cirq_shared_gates:
        circuit.append(gate)

    unitary = to_unitary(circuit)
    qbraid_circuit = circuit_wrapper(circuit)

    return qbraid_circuit, unitary


def braket_shared_gates_circuit():
    """Returns braket `Circuit` for qBraid `TestSharedGates`."""

    circuit = BraketCircuit()

    circuit.h([0, 1, 2, 3])
    circuit.x([0, 1])
    circuit.y(2)
    circuit.z(3)
    circuit.s(0)
    circuit.si(1)
    circuit.t(2)
    circuit.ti(3)
    circuit.rx(0, np.pi / 4)
    circuit.ry(1, np.pi / 2)
    circuit.rz(2, 3 * np.pi / 4)
    circuit.phaseshift(3, np.pi / 8)
    circuit.v(0)
    circuit.vi(1)
    circuit.iswap(2, 3)
    circuit.swap(0, 2)
    circuit.swap(1, 3)
    circuit.cnot(0, 1)
    circuit.cphaseshift(2, 3, np.pi / 4)

    unitary = to_unitary(circuit)
    qbraid_circuit = circuit_wrapper(circuit)

    return qbraid_circuit, unitary


# Define circuits and unitaries
qbraid_circuit_braket, braket_unitary = braket_shared_gates_circuit()
qbraid_circuit_cirq, cirq_unitary = cirq_shared_gates_circuit()
qbraid_circuit_qiskit, qiskit_unitary = qiskit_shared_gates_circuit()

cirq_qiskit_equal = np.allclose(cirq_unitary, qiskit_unitary)
cirq_braket_equal = np.allclose(cirq_unitary, braket_unitary)
qiskit_braket_equal = np.allclose(qiskit_unitary, braket_unitary)
assert cirq_qiskit_equal and cirq_braket_equal and qiskit_braket_equal

data_test_shared_gates = [
    (qbraid_circuit_braket, "cirq", cirq_unitary),
    (qbraid_circuit_braket, "qiskit", qiskit_unitary),
    (qbraid_circuit_qiskit, "braket", braket_unitary),
    (qbraid_circuit_qiskit, "cirq", cirq_unitary),
    (qbraid_circuit_cirq, "braket", braket_unitary),
    (qbraid_circuit_cirq, "qiskit", qiskit_unitary),
]


@pytest.mark.parametrize("qbraid_circuit,target_package,target_unitary", data_test_shared_gates)
def test_shared_gates(qbraid_circuit, target_package, target_unitary):
    """Tests transpiling circuits composed of gate types that share explicit support across
    multiple qbraid tranpsiler supported packages (qiskit, cirq, braket).
    """
    transpiled_circuit = qbraid_circuit.transpile(target_package)
    transpiled_unitary = to_unitary(transpiled_circuit)
    cirq.testing.assert_allclose_up_to_global_phase(transpiled_unitary, target_unitary, atol=1e-7)
    # assert np.allclose(transpiled_unitary, target_unitary)


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
    mapping = {q2: 0, q1: 1, q0: 2}

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


@pytest.mark.skip(reason="conversion error gate not supported")
@pytest.mark.parametrize("gate_str", yes_qiskit_no_braket)
def test_yes_qiskit_no_braket(gate_str):
    qiskit_init_gate = qiskit_gates[gate_str]
    nqubits, nparams = nqubits_nparams(gate_str)
    params = np.random.random_sample(nparams) * np.pi
    qiskit_gate = qiskit_init_gate(*params)
    qiskit_u, qbraid_qiskit_circ = qiskit_gate_test_circuit(qiskit_gate, nqubits)
    braket_circuit = qbraid_qiskit_circ.transpile("braket")
    braket_u = to_unitary(braket_circuit)
    cirq.testing.assert_allclose_up_to_global_phase(qiskit_u, braket_u, atol=1e-7)
    # assert np.allclose(qiskit_u, braket_u)


@pytest.mark.skip(reason="conversion error gate not supported")
@pytest.mark.parametrize("gate_str", yes_qiskit_no_cirq)
def test_yes_qiskit_no_cirq(gate_str):
    qiskit_init_gate = qiskit_gates[gate_str]
    nqubits, nparams = nqubits_nparams(gate_str)
    params = np.random.random_sample(nparams) * np.pi
    qiskit_gate = qiskit_init_gate(*params)
    qiskit_u, qbraid_qiskit_circ = qiskit_gate_test_circuit(qiskit_gate, nqubits)
    cirq_circuit = qbraid_qiskit_circ.transpile("cirq")
    cirq_u = to_unitary(cirq_circuit)
    cirq.testing.assert_allclose_up_to_global_phase(qiskit_u, cirq_u, atol=1e-7)
    # assert np.allclose(qiskit_u, cirq_u)


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


@pytest.mark.skip(reason="conversion error gate not supported")
def test_braket_transpile_unitary():
    matrix = braket_gates["CCX"]().to_matrix()
    braket_gate = braket_gates["Unitary"](matrix)
    braket_u, qbraid_braket_circ = braket_gate_test_circuit(braket_gate, 3, only_test_gate=True)
    qiskit_circuit = qbraid_braket_circ.transpile("qiskit")
    qiskit_u = to_unitary(qiskit_circuit)
    cirq.testing.assert_allclose_up_to_global_phase(braket_u, qiskit_u, atol=1e-7)
    # assert np.allclose(braket_u, qiskit_u)


@pytest.mark.skip(reason="lots of different errors")
@pytest.mark.parametrize("num_qubits", [1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
def test_1000_random_circuits(num_qubits):
    for _ in range(10):
        packages = ["braket", "qiskit", "cirq"]
        i, j = np.random.randint(0, high=3), np.random.randint(0, high=2)
        origin = packages[i]
        del packages[i]
        target = packages[j]
        rand_circuit = random_circuit(origin, num_qubits=num_qubits)
        origin_circuit = convert_to_contiguous(rand_circuit)
        origin_unitary = to_unitary(origin_circuit)
        target_circuit = circuit_wrapper(origin_circuit).transpile(target)
        target_unitary = to_unitary(target_circuit)
        if not cirq.testing.assert_allclose_up_to_global_phase(
            origin_unitary, target_unitary, atol=1e-7
        ):
            # if not np.allclose(origin_unitary, target_unitary):
            print()
            print(f"failed {origin} --> {target}")
            print()
            print(origin)
            print(origin_circuit)
            print()
            print(target)
            print(target_circuit)
            assert False
    assert True


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


@pytest.mark.skip(reason="assertion error")
def test_non_contiguous_qubits_qiskit():
    qiskit_circuit = QiskitCircuit(5)
    qiskit_circuit.h(0)
    qiskit_circuit.cx(0, 2)
    qiskit_circuit.cx(2, 4)
    qbraid_wrapper = circuit_wrapper(qiskit_circuit)
    braket_circuit = qbraid_wrapper.transpile("braket")
    cirq_circuit = qbraid_wrapper.transpile("cirq")
    qiskit_unitary = to_unitary(qiskit_circuit)
    braket_unitary = to_unitary(braket_circuit, ensure_contiguous=True)
    cirq_unitary = to_unitary(cirq_circuit, ensure_contiguous=True)
    cirq.testing.assert_allclose_up_to_global_phase(qiskit_unitary, braket_unitary, atol=1e-7)
    cirq.testing.assert_allclose_up_to_global_phase(cirq_unitary, qiskit_unitary, atol=1e-7)
    # assert np.allclose(qiskit_unitary, braket_unitary)
    # assert np.allclose(cirq_unitary, qiskit_unitary)
