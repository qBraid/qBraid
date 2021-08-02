import cirq
from qiskit.circuit.parametertable import ParameterTable

from braket.circuits.circuit import Circuit as BraketCircuit
import braket
from braket.circuits.gate import Gate

def test_cirq():

    qubits = [cirq.GridQubit(x, y) for x in range(3) for y in range(3)]

    print(qubits[0])

    cz01 = cirq.CZ(qubits[0], qubits[1])
    x2 = cirq.X(qubits[2])
    cz12 = cirq.CZ(qubits[1], qubits[2])
    moment0 = cirq.Moment([cz01, x2])
    moment1 = cirq.Moment([cz12])
    circuit = cirq.Circuit((moment0, moment1))

    print(circuit.moments[0].operations)
    #print(dir(circuit))

def test_braket():

    import numpy as np
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

    print(circuit)

    for moment in circuit.moments:
        print(moment)

    

    print(dir(circuit.moments[(0,[1])]))

test_braket()