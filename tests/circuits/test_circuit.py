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

from qiskit import QuantumCircuit
from qiskit.circuit import Parameter
from qiskit.circuit import QuantumCircuit as QiskitCircuit
from qiskit.circuit import QuantumRegister as QiskitQuantumRegister
from qiskit.circuit.classicalregister import ClassicalRegister as QiskitClassicalRegister
from qiskit.circuit.library.standard_gates.rx import CRXGate as QiskitCRXGate
from qiskit.circuit.library.standard_gates.u3 import U3Gate
from qiskit.circuit.library.standard_gates.x import CXGate as QiskitCXGate
from qiskit.circuit.measure import Measure as QiskitMeasure

from qbraid.circuits.transpiler import qbraid_wrapper
from qbraid.devices.execute import execute

# import qsimcirq

# cirq_gate_types = Union[CirqSingleQubitGate,CirqTwoQubitGate,CirqThreeQubitGate]
cirq_gate_types = (CirqSingleQubitGate, CirqTwoQubitGate, CirqThreeQubitGate)


def test_braket_to_all():
    """Testing converting braket circuit to cirq and qiskit circuit via qbraid wrapper."""

    circuit = BraketCircuit()
    # bell = circuit.h(0).cnot(control=0,target=1)

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
    qiskit_circuit = qbraid_circuit.transpile("qiskit")  # , auto_measure = True)
    print("qiskit circuit")
    print(qiskit_circuit)


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
    qubits = QiskitQuantumRegister(3)
    clbits = QiskitClassicalRegister(3)

    # create circuit
    circuit = QiskitCircuit(qubits, clbits)
    circuit.cnot(0, 1)
    circuit.h(2)
    circuit.h(0)
    circuit.cnot(1, 2)
    circuit.z(1)
    circuit.s(2)
    circuit.h(0)
    circuit.t(1)
    circuit.t(2)
    # circuit.rx(np.pi/3,0)
    circuit.measure([0, 1, 2], [2, 1, 0])
    print("qiskit circuit")
    print(circuit)

    # transpile
    qbraid_circuit = qbraid_wrapper(circuit)
    cirq_circuit = qbraid_circuit.transpile("cirq")
    print("cirq ciruit")
    print(cirq_circuit)

    # # simulate cirq circuit
    # simulator = Simulator()
    # result = simulator.run(cirq_circuit)
    # print(result)

    braket_circuit = qbraid_circuit.transpile("braket")
    print("braket circuit")
    print(braket_circuit)


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

    # Circuit(circuit)


def test_qiskit():
    """Testing building a non-paramterized qiskit circuit, no qbraid wrapper."""

    # circuit = QiskitQuantumCircuit(2,2)
    # circuit.rz(0,)
    # cx = QiskitCXGate()
    # print(isinstance(cx, QiskitControlledGate))
    # print(cx.num_ctrl_qubits)
    # print(cx.num_clbits)

    # cx2 = cx.control(2)
    # print(cx2.num_ctrl_qubits)

    # crx = QiskitCRXGate(np.pi / 2)
    # print(crx.name)
    # print(crx.params)
    # print(crx.num_qubits)

    # u3 = U3Gate(np.pi / 2, np.pi, np.pi / 4)
    # print(u3.params)
    # print(u3.name)

    # measure = QiskitMeasure()

    circuit = QiskitCircuit(2, 4)
    circuit.h(0)
    circuit.cnot(0, 1)
    circuit.measure([0], [0])
    circuit.measure([1], [1])
    # circuit.measure([0,1],[3,2])

    # Circuit(circuit)
    print(circuit.clbits)

    for instruction, qubit_list, clbit_list in circuit.data:

        if isinstance(instruction, QiskitMeasure):
            print(instruction, qubit_list, clbit_list)
            # print(clbit_list[0].index) # this line is deprecated
            print(dir(clbit_list[0]))
            break

    # Circuit(circuit)
    # define quantumregister
    qubits = QiskitQuantumRegister(3)
    clbits = QiskitClassicalRegister(3)

    # create circuit
    circuit = QiskitCircuit(qubits, clbits)
    circuit.cnot(0, 1)
    circuit.h(2)
    circuit.h(0)
    circuit.cnot(1, 2)
    circuit.z(1)
    circuit.s(2)
    circuit.h(0)
    circuit.t(1)
    circuit.t(2)
    circuit.rx(np.pi / 3, 0)
    circuit.measure([0, 1, 2], [2, 1, 0])

    for instruction, qubit_list, clbit_list in circuit.data:
        if isinstance(instruction, QiskitMeasure):
            print(dir(instruction))


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

    print(circuit == cirq_circuit_2)


def test_qiskit_prmtrzd():
    """Testing building a paramterized qiskit circuit, no qbraid wrapper."""

    n = 5
    theta = Parameter("θ")

    qc = QiskitCircuit(5, 1)
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
    # print(dir(qc.parameters))
    # print(list(qc.parameters))

    # for instruction, qubit_list, clbit_list in qc.data:
    #     print(instruction.params)


def test_qiskit_to_cirq_prmtrzd():
    """Testing converting parameterized qiskit circuit to cirq circuit via qbraid wrapper."""

    # qc = QiskitCircuit(1,1)
    # qc.rz(QiskitParameter('x'),0)
    # qc.rz(QiskitParameter('y'),0)

    n = 5
    theta = Parameter("θ")

    qc = QiskitCircuit(5, 1)
    # qc.rz(np.pi/4, [0,1,2])
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

    # qc.draw('mpl')
    print("qiskit circuit")
    print(qc)
    qbraid_circuit = qbraid_wrapper(qc)
    cqc = qbraid_circuit.transpile("cirq")
    # for op in cqc.all_operations():
    #    print(type(op.gate.exponent))
    print("cirq circuit")
    print(cqc)


def test_qiskit_execute():
    """Testing qbraid.devices.execute function on qiskit circuit"""

    qc = QuantumCircuit(2, 2)
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
    # qsim_results = qsim_simulator.run(circuit, repetitions=10)

    results = execute(circuit, simulator)
    print(results.get_counts())

    # print('qsim results:')
    # print(dir(qsim_results))
    # print(qsim_results.histograzm())
    # print(qsim_results.repetitions)
    # print(qsim_results.measurements)


if __name__ == "__main__":

    print("BRAKET TESTS")
    print("------------------------------")
    test_braket()         # passes
    test_braket_to_all()  # passes
    print("------------------------------")
    print()

    print("QISKIT TESTS")
    print("------------------------------")
    test_qiskit_prmtrzd()          # passes
    test_qiskit_execute()          # passes
    test_qiskit()                  # passes
    test_qiskit_to_cirq_prmtrzd()  # fails
    test_qiskit_to_all()           # fails
    print("------------------------------")
    print()

    print("CIRQ TESTS")
    print("------------------------------")
    test_cirq()                 # passes
    test_cirq_execute()         # passes
    test_cirq_qiskit_two_way()  # fails
    test_cirq_to_all()          # passes
    print("------------------------------")
    print()

    print("ALL TESTS PASSED")
