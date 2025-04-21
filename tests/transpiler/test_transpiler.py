# Copyright (C) 2024 qBraid
#
# This file is part of the qBraid-SDK
#
# The qBraid-SDK is free software released under the GNU General Public License v3
# or later. You can redistribute and/or modify it under the terms of the GPL v3.
# See the LICENSE file in the project root or <https://www.gnu.org/licenses/gpl-3.0.html>.
#
# THERE IS NO WARRANTY for the qBraid-SDK, as per Section 15 of the GPL v3.

# pylint: disable=redefined-outer-name

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
from qiskit.circuit import Qubit as QiskitQubit

from qbraid.interface import assert_allclose_up_to_global_phase
from qbraid.programs import QPROGRAM_ALIASES, load_program
from qbraid.programs.exceptions import ProgramLoaderError, ProgramTypeError
from qbraid.programs.registry import is_registered_alias_native
from qbraid.transpiler.converter import transpile
from qbraid.transpiler.exceptions import NodeNotFoundError
from qbraid.transpiler.graph import ConversionGraph

from ..fixtures import packages_bell
from ..fixtures.braket.gates import braket_gates as braket_gates_dict
from ..fixtures.cirq.gates import cirq_gates as cirq_gates_dict
from ..fixtures.cirq.gates import create_cirq_gate
from ..fixtures.qiskit.gates import qiskit_gates as qiskit_gates_dict
from .cirq_utils import _equal


@pytest.fixture
def conversion_graph():
    """Return the conversion graph."""
    return ConversionGraph()


@pytest.mark.parametrize(
    "two_bell_circuits",
    [("qiskit", "cirq"), ("pyquil", "cirq"), ("braket", "cirq"), ("pytket", "cirq")],
    indirect=True,
)
def test_to_cirq(two_bell_circuits):
    """Test coverting circuits to Cirq."""
    circuit1, circuit2, _, _ = two_bell_circuits
    if circuit1 is None or circuit2 is None:
        pytest.skip("Necessary packages not installed")

    converted_circuit = transpile(circuit1, "cirq", require_native=True)
    assert _equal(converted_circuit, circuit2, allow_reversed_qubit_order=True)


@pytest.mark.parametrize("item", [1, None])
def test_to_cirq_bad_types(item):
    """Test raising ProgramTypeError converting circuit of non-supported type"""
    with pytest.raises(ProgramTypeError):
        transpile(item, "cirq")


@pytest.mark.parametrize(
    "item",
    ["OPENQASM 1.0; bad operation", "OPENQASM -3.0; bad operation", "DECLARE ro BIT[1]", "circuit"],
)
def test_to_cirq_bad_openqasm_program(item):
    """Test raising QasmParsingError converting invalid OpenQASM program string"""
    with pytest.raises(ProgramTypeError):
        transpile(item, "cirq")


@pytest.mark.parametrize("bell_circuit", ["cirq"], indirect=True)
@pytest.mark.parametrize("to_type", QPROGRAM_ALIASES)
def test_cirq_round_trip(bell_circuit, to_type, conversion_graph: ConversionGraph):
    """Test converting Cirq circuits to other supported types."""
    if not conversion_graph.has_path("cirq", to_type) or not conversion_graph.has_path(
        to_type, "cirq"
    ):
        pytest.skip(f"cirq to {to_type} round-trip not yet supported")
    circuit_in, _ = bell_circuit

    require_native = is_registered_alias_native(to_type)
    circuit_mid = transpile(circuit_in, to_type, require_native=require_native)
    circuit_out = transpile(circuit_mid, "cirq", require_native=require_native)
    assert _equal(circuit_in, circuit_out), f"Failed round-trip from cirq to {to_type}"


@pytest.mark.parametrize("bell_circuit", ["cirq"], indirect=True)
@pytest.mark.parametrize("item", ["package", 1, None])
def test_from_cirq_bad_package(bell_circuit, item):
    """Test raising PackageValueError converting circuit to non-supported package"""
    circuit, _ = bell_circuit
    with pytest.raises(NodeNotFoundError):
        transpile(circuit, item)


@pytest.mark.parametrize("program", ["Not a circuit", None])
def test_load_program_error(program):
    """Test raising circuit wrapper error"""
    with pytest.raises(ProgramLoaderError):
        load_program(program)


@pytest.mark.parametrize("bell_circuit", ["braket"], indirect=True)
def test_transpile_package_error(bell_circuit):
    """Test raising circuit wrapper error"""
    circuit, _ = bell_circuit
    wrapped = load_program(circuit)
    with pytest.raises(NodeNotFoundError):
        transpile(wrapped.program, "Not a package")


@pytest.mark.parametrize("bell_circuit", ["braket"], indirect=True)
def test_transpile_program_error(bell_circuit):
    """Test raising circuit wrapper error"""
    circuit, _ = bell_circuit
    wrapped = load_program(circuit)
    wrapped._program = None
    with pytest.raises(ProgramTypeError):
        transpile(wrapped.program, "qiskit")


@pytest.mark.parametrize("target_package", ["cirq", "qiskit", "braket"])
@pytest.mark.parametrize("shared15_circuit", ["cirq", "qiskit", "braket"], indirect=True)
def test_15(shared15_circuit, shared15_unitary, target_package):
    """Tests transpiling circuits composed of gate types that share explicit support across
    multiple qbraid tranpsiler supported packages (qiskit, cirq, braket).
    """
    circuit, _ = shared15_circuit
    qbraid_circuit = load_program(circuit)
    transpiled_circuit = transpile(qbraid_circuit.program, target_package, require_native=True)
    transpiled_unitary = load_program(transpiled_circuit).unitary()
    assert_allclose_up_to_global_phase(transpiled_unitary, shared15_unitary, atol=1e-7)


@pytest.mark.parametrize("target", packages_bell)
@pytest.mark.parametrize("bell_circuit", packages_bell, indirect=True)
def test_bell(bell_circuit, bell_unitary, target, conversion_graph: ConversionGraph):
    """Tests transpiling bell circuits."""
    circuit, source = bell_circuit
    if not conversion_graph.has_path(source, target):
        pytest.skip(f"{source} to {target} conversion not yet supported")
    qbraid_circuit = load_program(circuit)
    transpiled_circuit = transpile(qbraid_circuit.program, target, require_native=True)
    try:
        transpiled_unitary = load_program(transpiled_circuit).unitary()
        assert_allclose_up_to_global_phase(transpiled_unitary, bell_unitary, atol=1e-7)
    except NotImplementedError:
        pytest.skip(f"Unitary calculation not yet supported for {target}")


def nqubits_nparams(gate: str) -> tuple[int, int]:
    """Return number of qubits and parameters for a given gate."""
    if gate in ["H", "X", "Y", "Z", "S", "Sdg", "T", "Tdg", "I", "SX", "SXdg"]:
        return 1, 0
    if gate in ["Phase", "RX", "RY", "RZ", "U1", "HPow", "XPow", "YPow", "ZPow"]:
        return 1, 1
    if gate in ["R", "U2"]:
        return 1, 2
    if gate in ["U", "U3"]:
        return 1, 3
    if gate in ["CX", "CSX", "CH", "DCX", "Swap", "iSwap", "CY", "CZ"]:
        return 2, 0
    if gate in ["RXX", "RXY", "RZX", "RYY", "CU1", "CRY", "RZZ", "CRZ", "CRX", "pSwap", "CPhase"]:
        return 2, 1
    if gate in ["CCX", "RCCX"]:
        return 3, 0
    if gate in ["CCZ"]:
        return 3, 1
    raise ValueError(f"Gate {gate} not accounted for")


def assign_params(init_gate1, init_gate2, nparams):
    """Generate and assign random parameters to gates."""
    params = np.random.random_sample(nparams) * np.pi
    return init_gate1(*params), init_gate2(*params)


def assign_params_cirq(gate_str, init_gate, nparams):
    """Generate and assign random parameters to custom Cirq gate."""
    params = np.random.random_sample(nparams) * np.pi
    cirq_data = {"type": gate_str, "params": params, "matrix": None}
    new_cirq_gate = create_cirq_gate(cirq_data)
    return new_cirq_gate, init_gate(*params)


def braket_gate_test_circuit(test_gate, nqubits, only_test_gate=False):
    """Construct general Braket circuit with inserted test gate."""
    qubits = list(range(nqubits)) if nqubits > 1 else 0

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

    qbraid_circuit = load_program(circuit)
    unitary = qbraid_circuit.unitary()

    return unitary, qbraid_circuit


def qiskit_gate_test_circuit(test_gate, nqubits):
    """Construct general Qiskit circuit with inserted test gate."""
    qreg = QiskitQuantumRegister(3, name="q")
    circuit = QiskitCircuit(qreg)
    circuit.h([0, 1, 2])
    qubits = [QiskitQubit(qreg, i) for i in range(nqubits)]
    circuit.append(test_gate, qubits)
    circuit.cx(0, 1)
    circuit.ry(np.pi, 2)

    qbraid_circuit = load_program(circuit)
    unitary = qbraid_circuit.unitary()

    return unitary, qbraid_circuit


def cirq_gate_test_circuit(test_gate, nqubits):
    """Construct general Cirq circuit with inserted test gate."""
    circuit = CirqCircuit()
    q0, q1, q2 = [cirq.LineQubit(i) for i in range(3)]

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

    qbraid_circuit = load_program(circuit)
    unitary = qbraid_circuit.unitary()

    return unitary, qbraid_circuit


braket_gate_set = set(braket_gates_dict.keys())
qiskit_gate_set = set(qiskit_gates_dict.keys())
cirq_gate_set = set(cirq_gates_dict.keys())

intersect_braket_qiskit = list(braket_gate_set.intersection(list(qiskit_gate_set)))
intersect_qiskit_cirq = list(qiskit_gate_set.intersection(list(cirq_gate_set)))
intersect_cirq_braket = list(cirq_gate_set.intersection(list(braket_gate_set)))

# skipping
intersect_braket_qiskit.remove("RXX")
intersect_braket_qiskit.remove("RYY")


@pytest.mark.parametrize("gate_str", intersect_braket_qiskit)
def test_gate_intersect_braket_qiskit(gate_str):
    """Test transpiling circuits with gates that are supported by both Braket and Qiskit."""
    braket_init_gate = braket_gates_dict[gate_str]
    qiskit_init_gate = qiskit_gates_dict[gate_str]
    nqubits, nparams = nqubits_nparams(gate_str)
    qiskt_gate, braket_gate = assign_params(qiskit_init_gate, braket_init_gate, nparams)
    braket_u, qbraid_braket_circ = braket_gate_test_circuit(braket_gate, nqubits)
    qiskit_u, qbraid_qiskit_circ = qiskit_gate_test_circuit(qiskt_gate, nqubits)
    assert_allclose_up_to_global_phase(braket_u, qiskit_u, atol=1e-7)
    braket_circuit_transpile = transpile(qbraid_qiskit_circ.program, "braket", require_native=True)
    qiskit_circuit_transpile = transpile(qbraid_braket_circ.program, "qiskit", require_native=True)
    braket_transpile_u = load_program(braket_circuit_transpile).unitary()
    qiskit_transpile_u = load_program(qiskit_circuit_transpile).unitary()
    assert_allclose_up_to_global_phase(braket_u, braket_transpile_u, atol=1e-7)
    assert_allclose_up_to_global_phase(qiskit_u, qiskit_transpile_u, atol=1e-7)


@pytest.mark.parametrize("gate_str", intersect_qiskit_cirq)
def test_gate_intersect_qiskit_cirq(gate_str):
    """Test transpiling circuits with gates that are supported by both Qiskit and Cirq."""
    qiskit_init_gate = qiskit_gates_dict[gate_str]
    nqubits, nparams = nqubits_nparams(gate_str)
    cirq_gate, qiskit_gate = assign_params_cirq(gate_str, qiskit_init_gate, nparams)
    cirq_u, qbraid_cirq_circ = cirq_gate_test_circuit(cirq_gate, nqubits)
    qiskit_u, qbraid_qiskit_circ = qiskit_gate_test_circuit(qiskit_gate, nqubits)
    assert_allclose_up_to_global_phase(cirq_u, qiskit_u, atol=1e-7)
    qiskit_circuit_transpile = transpile(qbraid_cirq_circ.program, "qiskit", require_native=True)
    cirq_circuit_transpile = transpile(qbraid_qiskit_circ.program, "cirq", require_native=True)
    qiskit_transpile_u = load_program(qiskit_circuit_transpile).unitary()
    cirq_transpile_u = load_program(cirq_circuit_transpile).unitary()
    assert_allclose_up_to_global_phase(cirq_u, cirq_transpile_u, atol=1e-7)
    assert_allclose_up_to_global_phase(qiskit_u, qiskit_transpile_u, atol=1e-7)


@pytest.mark.parametrize("gate_str", intersect_cirq_braket)
def test_gate_intersect_braket_cirq(gate_str):
    """Test transpiling circuits with gates that are supported by both Braket and Cirq."""
    braket_init_gate = braket_gates_dict[gate_str]
    nqubits, nparams = nqubits_nparams(gate_str)
    cirq_gate, braket_gate = assign_params_cirq(gate_str, braket_init_gate, nparams)
    cirq_u, qbraid_cirq_circ = cirq_gate_test_circuit(cirq_gate, nqubits)
    braket_u, qbraid_braket_circ = braket_gate_test_circuit(braket_gate, nqubits)
    assert_allclose_up_to_global_phase(cirq_u, braket_u, atol=1e-7)
    braket_circuit_transpile = transpile(qbraid_cirq_circ.program, "braket", require_native=True)
    cirq_circuit_transpile = transpile(qbraid_braket_circ.program, "cirq", require_native=True)
    braket_transpile_u = load_program(braket_circuit_transpile).unitary()
    cirq_transpile_u = load_program(cirq_circuit_transpile).unitary()
    assert_allclose_up_to_global_phase(cirq_u, cirq_transpile_u, atol=1e-7)
    assert_allclose_up_to_global_phase(braket_u, braket_transpile_u, atol=1e-7)


yes_braket_no_qiskit = list(set(braket_gates_dict).difference(qiskit_gates_dict))
yes_qiskit_no_braket = list(set(qiskit_gates_dict).difference(braket_gates_dict))
yes_braket_no_cirq = list(set(braket_gates_dict).difference(cirq_gates_dict))
yes_cirq_no_braket = list(set(cirq_gates_dict).difference(braket_gates_dict))
yes_cirq_no_qiskit = list(set(cirq_gates_dict).difference(qiskit_gates_dict))
yes_qiskit_no_cirq = list(set(qiskit_gates_dict).difference(cirq_gates_dict))

NOT_SUPPORTED = ["RCCX", "RXX", "RYY", "RZX", "CSX", "CRX", "CRY", "U"]


@pytest.mark.parametrize("gate_str", yes_braket_no_qiskit)
def test_yes_braket_no_qiskit(gate_str):
    """Test transpiling circuits with gates that are supported by Braket but not Qiskit."""
    braket_init_gate = braket_gates_dict[gate_str]
    nqubits, nparams = nqubits_nparams(gate_str)
    params = np.random.random_sample(nparams) * np.pi
    braket_gate = braket_init_gate(*params)
    braket_u, qbraid_braket_circ = braket_gate_test_circuit(braket_gate, nqubits)
    qiskit_circuit = transpile(qbraid_braket_circ.program, "qiskit", require_native=True)
    qiskit_u = load_program(qiskit_circuit).unitary()
    assert_allclose_up_to_global_phase(braket_u, qiskit_u, atol=1e-7)


@pytest.mark.parametrize("gate_str", yes_qiskit_no_braket)
def test_yes_qiskit_no_braket(gate_str):
    """Test transpiling circuits with gates that are supported by Qiskit but not Braket."""
    qiskit_init_gate = qiskit_gates_dict[gate_str]
    nqubits, nparams = nqubits_nparams(gate_str)
    params = np.random.random_sample(nparams) * np.pi
    qiskit_gate = qiskit_init_gate(*params)
    qiskit_u, qbraid_qiskit_circ = qiskit_gate_test_circuit(qiskit_gate, nqubits)
    if gate_str in NOT_SUPPORTED:
        pytest.skip(f"{gate_str} not supported by Amazon Braket")
    braket_circuit = transpile(qbraid_qiskit_circ.program, "braket", require_native=True)
    braket_u = load_program(braket_circuit).unitary()
    assert_allclose_up_to_global_phase(qiskit_u, braket_u, atol=1e-7)


@pytest.mark.parametrize("gate_str", yes_qiskit_no_cirq)
def test_yes_qiskit_no_cirq(gate_str):
    """Test transpiling circuits with gates that are supported by Qiskit but not Cirq."""
    qiskit_init_gate = qiskit_gates_dict[gate_str]
    nqubits, nparams = nqubits_nparams(gate_str)
    params = np.random.random_sample(nparams) * np.pi
    qiskit_gate = qiskit_init_gate(*params)
    qiskit_u, qbraid_qiskit_circ = qiskit_gate_test_circuit(qiskit_gate, nqubits)
    if gate_str in NOT_SUPPORTED:
        pytest.skip(f"{gate_str} not supported by Cirq")
    cirq_circuit = transpile(qbraid_qiskit_circ.program, "cirq", require_native=True)
    cirq_u = load_program(cirq_circuit).unitary()
    assert_allclose_up_to_global_phase(qiskit_u, cirq_u, atol=1e-7)


@pytest.mark.parametrize("gate_str", yes_braket_no_cirq)
def test_yes_braket_no_cirq(gate_str):
    """Test transpiling circuits with gates that are supported by Braket but not Cirq."""
    braket_init_gate = braket_gates_dict[gate_str]
    nqubits, nparams = nqubits_nparams(gate_str)
    params = np.random.random_sample(nparams) * np.pi
    braket_gate = braket_init_gate(*params)
    braket_u, qbraid_braket_circ = braket_gate_test_circuit(braket_gate, nqubits)
    cirq_circuit = transpile(qbraid_braket_circ.program, "cirq", require_native=True)
    cirq_u = load_program(cirq_circuit).unitary()
    assert_allclose_up_to_global_phase(braket_u, cirq_u, atol=1e-7)


@pytest.mark.parametrize("gate_str", yes_cirq_no_qiskit)
def test_yes_cirq_no_qiskit(gate_str):
    """Test transpiling circuits with gates that are supported by Cirq but not Qiskit."""
    cirq_init_gate = cirq_gates_dict[gate_str]
    nqubits, _ = nqubits_nparams(gate_str)
    exp = np.random.random()
    cirq_gate = cirq_init_gate(exponent=exp)
    cirq_u, qbraid_cirq_circ = cirq_gate_test_circuit(cirq_gate, nqubits)
    qiskit_circuit = transpile(qbraid_cirq_circ.program, "qiskit", require_native=True)
    qiskit_u = load_program(qiskit_circuit).unitary()
    assert_allclose_up_to_global_phase(cirq_u, qiskit_u, atol=1e-7)


@pytest.mark.parametrize("gate_str", yes_cirq_no_braket)
def test_yes_cirq_no_braket(gate_str):
    """Test transpiling circuits with gates that are supported by Cirq but not Braket."""
    cirq_init_gate = cirq_gates_dict[gate_str]
    nqubits, nparams = nqubits_nparams(gate_str)
    if gate_str == "U3":
        params = np.random.random_sample(nparams)
        cirq_gate = cirq_init_gate(*params)
    else:
        exp = np.random.random()
        cirq_gate = cirq_init_gate(exponent=exp)
    cirq_u, qbraid_cirq_circ = cirq_gate_test_circuit(cirq_gate, nqubits)
    braket_circuit = transpile(qbraid_cirq_circ.program, "braket", require_native=True)
    braket_u = load_program(braket_circuit).unitary()
    assert_allclose_up_to_global_phase(cirq_u, braket_u, atol=1e-7)


def test_braket_transpile_ccnot():
    """Test transpiling CCNOT circuit from Braket to Qiskit."""
    braket_circuit = BraketCircuit()
    braket_circuit.ccnot(2, 0, 1)
    braket_circuit.ccnot(3, 1, 0)
    qbraid_braket = load_program(braket_circuit)
    qiskit_circuit = transpile(qbraid_braket.program, "qiskit", require_native=True)
    braket_ccnot_unitary = load_program(braket_circuit).unitary()
    qiskit_ccnot_unitary = load_program(qiskit_circuit).unitary()
    assert_allclose_up_to_global_phase(braket_ccnot_unitary, qiskit_ccnot_unitary, atol=1e-7)


def test_non_contiguous_qubits_braket():
    """Test transpiling Braket circuit with non-contiguous qubit indexing to Cirq and Qiskit."""
    braket_circuit = BraketCircuit()
    braket_circuit.h(0)
    braket_circuit.cnot(0, 2)
    braket_circuit.cnot(2, 4)
    qpgoram_test = load_program(braket_circuit)
    qpgoram_test.remove_idle_qubits()
    test_circuit = qpgoram_test.program
    qbraid_wrapper = load_program(test_circuit)
    cirq_circuit = transpile(qbraid_wrapper.program, "cirq", require_native=True)
    qiskit_circuit = transpile(qbraid_wrapper.program, "qiskit", require_native=True)
    braket_unitary = load_program(test_circuit).unitary()
    cirq_unitary = load_program(cirq_circuit).unitary()
    qiskit_unitary = load_program(qiskit_circuit).unitary()
    assert_allclose_up_to_global_phase(braket_unitary, cirq_unitary, atol=1e-7)
    assert_allclose_up_to_global_phase(qiskit_unitary, braket_unitary, atol=1e-7)


def test_non_contiguous_qubits_cirq():
    """Test transpiling Cirq circuit with non-contiguous qubit indexing to Qiskit and Braket."""
    cirq_circuit = CirqCircuit()
    q0 = cirq.LineQubit(4)
    q2 = cirq.LineQubit(2)
    q4 = cirq.LineQubit(0)
    cirq_circuit.append(cirq.H(q0))
    cirq_circuit.append(cirq.CNOT(q0, q2))
    cirq_circuit.append(cirq.CNOT(q2, q4))
    qpgoram_test = load_program(cirq_circuit)
    qpgoram_test.remove_idle_qubits()
    test_circuit = qpgoram_test.program
    qbraid_wrapper = load_program(test_circuit)
    qiskit_circuit = transpile(qbraid_wrapper.program, "qiskit", require_native=True)
    braket_circuit = transpile(qbraid_wrapper.program, "braket", require_native=True)
    cirq_unitary = load_program(test_circuit).unitary()
    qiskit_unitary = load_program(qiskit_circuit).unitary()
    braket_unitary = load_program(braket_circuit).unitary()
    assert_allclose_up_to_global_phase(cirq_unitary, qiskit_unitary, atol=1e-7)
    assert_allclose_up_to_global_phase(braket_unitary, cirq_unitary, atol=1e-7)
