import braket
from braket.circuits import Circuit as BraketCircuit
from braket.circuits.gate import Gate as BraketGate
from braket.circuits.instruction import Instruction as BraketInstruction
import cirq
from cirq import Simulator
from cirq.circuits import Circuit as CirqCircuit
from cirq.ops.gate_features import SingleQubitGate as CirqSingleQubitGate
from cirq.ops.gate_features import ThreeQubitGate as CirqThreeQubitGate
from cirq.ops.gate_features import TwoQubitGate as CirqTwoQubitGate
import numpy as np
import qiskit
from qiskit.circuit import Parameter
from qbraid.transpiler.transpiler import qbraid_wrapper
from qbraid.devices.execute import execute
from typing import Union


cirq_gate_types = Union[CirqSingleQubitGate, CirqTwoQubitGate, CirqThreeQubitGate]


def test_braket_to_all():
    """Testing converting braket circuit to cirq and qiskit circuit via qbraid wrapper."""

    circuit = braket.circuits.Circuit()

    instructions = [
        BraketInstruction(BraketGate.H(), 0),
        BraketInstruction(BraketGate.X(), 1),
        BraketInstruction(BraketGate.Y(), 2),
        BraketInstruction(BraketGate.Z(), 1),
        BraketInstruction(BraketGate.S(), 0),
        BraketInstruction(BraketGate.Si(), 1),
        BraketInstruction(BraketGate.T(), 2),
        BraketInstruction(BraketGate.Ti(), 1),
        BraketInstruction(BraketGate.I(), 0),
        BraketInstruction(BraketGate.V(), 0),
        BraketInstruction(BraketGate.Vi(), 2),
        BraketInstruction(BraketGate.PhaseShift(np.pi), 2),
        BraketInstruction(BraketGate.Rx(np.pi), 0),
        BraketInstruction(BraketGate.Ry(np.pi), 1),
        BraketInstruction(BraketGate.Rz(np.pi / 2), 2),
        BraketInstruction(BraketGate.CNot(), [1, 0]),
        BraketInstruction(BraketGate.Swap(), [1, 2]),
        BraketInstruction(BraketGate.ISwap(), [1, 2]),
        BraketInstruction(BraketGate.PSwap(np.pi), [0, 1]),
        BraketInstruction(BraketGate.CY(), [0, 1]),
        BraketInstruction(BraketGate.CZ(), [1, 0]),
        BraketInstruction(BraketGate.CPhaseShift(np.pi / 4), [2, 0]),
        BraketInstruction(BraketGate.XX(np.pi), [0, 1]),
        BraketInstruction(BraketGate.XY(np.pi), [0, 1]),
        BraketInstruction(BraketGate.YY(np.pi), [0, 1]),
        BraketInstruction(BraketGate.ZZ(np.pi), [0, 1]),
        BraketInstruction(BraketGate.CCNot(), [0, 1, 2]),
    ]

    for inst in instructions:
        circuit.add_instruction(inst)

    print("braket circuit")
    print(circuit)
    qbraid_circuit = qbraid_wrapper(circuit)
    cirq_circuit = qbraid_circuit.transpile(package="cirq")
    print("cirq circuit")
    print(cirq_circuit)
    # qiskit_circuit = qbraid_circuit.transpile("qiskit")  # , auto_measure = True)
    # print("qiskit circuit")
    # print(qiskit_circuit)


def test_cirq_to_all():
    """Testing converting cirq circuit to braket and qiskit circuit via qbraid wrapper."""

    # define qubits
    q0 = cirq.LineQubit(0)
    q1 = cirq.LineQubit(1)

    # define operations
    op_h = cirq.H(q0)
    op_cnot = cirq.CNOT(q0, q1)
    op_z = cirq.Z(q1)
    op_t = cirq.T(q0)
    op_s = cirq.S(q1)

    # add operations to circuit
    circuit = cirq.Circuit()
    circuit.append(op_h)
    circuit.append(op_cnot)
    circuit.append(op_z)
    circuit.append(op_s)
    circuit.append(op_t)

    # measure both qubits
    m0 = cirq.measure(q0, key="0")
    m1 = cirq.measure(q1, key="1")
    circuit.append([m0, m1])

    # transpile
    qbraid_circuit = qbraid_wrapper(circuit)

    print("cirq circuit\n\n", circuit)
    qiskit_circuit = qbraid_circuit.transpile("qiskit")
    print("qiskit circuit\n\n", qiskit_circuit)
    braket_circuit = qbraid_circuit.transpile("braket")
    print("braket circuit\n\n", braket_circuit)


def test_qiskit_to_all():
    """Testing converting qiskit circuit to cirq and braket circuit via qbraid wrapper."""

    # define quantumregister
    qubits = qiskit.QuantumRegister(3)
    clbits = qiskit.ClassicalRegister(3)

    # create circuit
    circuit = qiskit.QuantumCircuit(qubits, clbits)
    circuit.cnot(0, 1)
    # circuit.swap(0, 1)
    circuit.h(2)
    circuit.h(0)
    circuit.cnot(1, 2)
    circuit.z(1)
    circuit.s(2)
    circuit.h(0)
    circuit.t(1)
    circuit.t(2)
    circuit.rx(np.pi/3, 0)
    circuit.measure([0, 1, 2], [2, 1, 0])
    print("qiskit circuit")
    print(circuit)

    # transpile
    qbraid_circuit = qbraid_wrapper(circuit)

    cirq_circuit = qbraid_circuit.transpile("cirq")
    print("cirq ciruit")
    print(cirq_circuit)

    # simulate cirq circuit
    # simulator = Simulator()
    # result = simulator.run(cirq_circuit)
    # print(result)

    # braket_circuit = qbraid_circuit.transpile("braket")
    # print("braket circuit")
    # print(braket_circuit)


def test_cirq():
    """Testing building cirq circuit, no qbraid wrapper."""

    # define qubits
    q0 = cirq.LineQubit(0)
    q1 = cirq.LineQubit(1)

    circuit = CirqCircuit()
    theta = np.pi / 2
    rz_gate = cirq.rz(theta)
    circuit.append(rz_gate(q0))
    circuit.append(rz_gate(q1))

    print(dir(rz_gate))
    print(rz_gate.exponent)
    print(rz_gate.global_shift)

    circuit.append(cirq.H(q0))
    circuit.append(cirq.CNOT(q0, q1))

    m0 = cirq.measure(q0, key="0")
    m1 = cirq.measure(q1, key="1")

    circuit.append([m0, m1])
    print("cirq circuit")
    print(circuit)

    simulator = Simulator()
    result = simulator.run(circuit)
    print("simulator result")
    print(result)


def test_qiskit():
    """Testing building a non-paramterized qiskit circuit, no qbraid wrapper."""

    # Build a basic circuit
    circ = qiskit.QuantumCircuit(3, 6)
    circ.h(0)
    circ.cx(0, 1)
    circ.cx(0, 2)

    # test Aer backend
    backend = qiskit.Aer.get_backend("statevector_simulator")
    job = qiskit.execute(circ, backend)
    result = job.result()
    outputstate = result.get_statevector(circ, decimals=3)
    print(outputstate)

    # test OpenQASM backend
    circ.barrier(range(3))
    circ.measure(range(3), range(3))
    print(circ.draw())

    backend_sim = qiskit.Aer.get_backend("qasm_simulator")
    job_sim = qiskit.execute(circ, backend_sim, shots=1024)
    result_sim = job_sim.result()
    counts = result_sim.get_counts(circ)
    print(counts)


def test_braket():
    """Testing building a braket circuit, no qbraid wrapper."""

    circuit = BraketCircuit().h(range(4)).cnot(control=0, target=2).cnot(control=1, target=3)
    print(circuit)

    for instruction in circuit.instructions:
        print(instruction)


def test_cirq_qiskit_two_way():
    """Testing converting cirq circuit to qiskit and back to cirq and evaluating equivalence."""

    # define qubits
    q0 = cirq.LineQubit(0)
    q1 = cirq.LineQubit(1)

    # define operations
    op_h = cirq.H(q0) ** 1.8
    op_cnot = cirq.CNOT(q0, q1)
    op_z = cirq.Z(q1)
    op_t = cirq.T(q0)
    op_s = cirq.S(q1)

    h = cirq.H.controlled(1)
    op_controlled_h = h(q0, q1)

    # add operations to circuit
    circuit = cirq.Circuit()
    circuit.append(op_h)
    circuit.append(cirq.H(q0))
    circuit.append(cirq.X(q1))
    circuit.append(op_cnot)
    circuit.append(op_z)
    circuit.append(op_s)
    circuit.append(op_t)
    circuit.append(op_controlled_h)

    # measure both qubits
    m0 = cirq.measure(q0, key="0")
    m1 = cirq.measure(q1, key="1")
    circuit.append([m0, m1])

    # transpile
    qbraid_circuit = qbraid_wrapper(circuit)

    print("cirq circuit\n")
    print(circuit)
    qiskit_circuit = qbraid_circuit.transpile("qiskit")
    print("qiskit circuit\n")
    print(qiskit_circuit)

    cirq_circuit_2 = qbraid_wrapper(qiskit_circuit).transpile("cirq")
    print("cirq circuit 2")
    print(cirq_circuit_2)

    assert np.allclose(circuit.unitary(), cirq_circuit_2.unitary())


def test_qiskit_prmtrzd():
    """Testing building a paramterized qiskit circuit, no qbraid wrapper."""

    n = 5
    theta = qiskit.circuit.Parameter(r"$\theta$")

    qc = qiskit.QuantumCircuit(5, 1)
    qc.rz(np.pi / 4, range(5))
    qc.h(0)

    for i in range(n - 1):
        qc.cx(i, i + 1)

    qc.barrier()
    qc.rz(theta, range(2, 5))
    qc.barrier()

    for i in reversed(range(n - 1)):
        qc.cx(i, i + 1)
    qc.h(0)
    qc.measure(0, 0)

    print(qc)


def test_qiskit_to_cirq_prmtrzd():
    """Testing converting parameterized qiskit circuit to cirq circuit via qbraid wrapper."""

    n = 5
    theta = Parameter("\u03B8")

    qc = qiskit.QuantumCircuit(5, 1)
    qc.rz(np.pi / 4, range(5))
    qc.h(0)

    for i in range(n - 1):
        qc.cx(i, i + 1)

    # qc.barrier()
    qc.rz(theta, range(5))
    # qc.barrier()

    for i in reversed(range(n - 1)):
        qc.cx(i, i + 1)
    qc.h(0)
    qc.measure(0, 0)

    print("qiskit circuit")
    print(qc)
    qbraid_circuit = qbraid_wrapper(qc)
    cqc = qbraid_circuit.transpile("cirq")
    print("cirq circuit")
    print(cqc)


def test_qiskit_execute():
    """Testing qbraid.devices.execute function on qiskit circuit"""

    qc = qiskit.QuantumCircuit(2, 2)
    qc.h(0)
    qc.h(1)
    qc.cx(0, 1)
    qc.measure([0, 1], [1, 0])

    qbraid_result = execute(qc, "IBM_qasm_simulator")
    print(qbraid_result.get_counts())


def test_cirq_execute():
    """Testing qbraid.devices.execute function on cirq circuit"""

    # Pick up to ~25 qubits to simulate (requires ~256MB of RAM)
    qubits = [cirq.GridQubit(i, j) for i in range(2) for j in range(2)]

    # Define a circuit to run
    # (Example is from the 2019 "Quantum Supremacy" experiement)
    circuit = cirq.experiments.random_rotations_between_grid_interaction_layers_circuit(
        qubits=qubits, depth=16
    )

    # Measure qubits at the end of the circuit
    circuit.append(cirq.measure(*qubits, key="all_qubits"))

    # cirq
    # define qubits
    q0 = cirq.LineQubit(0)
    q1 = cirq.LineQubit(1)

    circuit = CirqCircuit()
    theta = np.pi / 2
    rz_gate = cirq.rz(theta)
    circuit.append(rz_gate(q0))
    circuit.append(rz_gate(q1))

    circuit.append(cirq.H(q0))
    circuit.append(cirq.CNOT(q0, q1))

    m0 = cirq.measure(q0, key="0")
    m1 = cirq.measure(q1, key="1")

    circuit.append([m0, m1])

    simulator = cirq.Simulator()

    results = execute(circuit, simulator)
    print(results.get_counts())


if __name__ == "__main__":

    # print("BRAKET TESTS")
    # print("------------------------------")
    # test_braket()
    # test_braket_to_all()
    # print("------------------------------")
    # print()
    #
    # print("QISKIT TESTS")
    # print("------------------------------")
    # test_qiskit_prmtrzd()
    # test_qiskit_execute()
    # test_qiskit()
    # test_qiskit_to_cirq_prmtrzd()
    test_qiskit_to_all()
    # print("------------------------------")
    # print()
    #
    # print("CIRQ TESTS")
    # print("------------------------------")
    # test_cirq()
    # test_cirq_execute()
    # test_cirq_qiskit_two_way()
    # test_cirq_to_all()
    # print("------------------------------")
    # print()
    #
    # print("ALL TESTS PASSED")
