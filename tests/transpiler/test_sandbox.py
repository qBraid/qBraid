import cirq
from qiskit.circuit.parametertable import ParameterTable


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