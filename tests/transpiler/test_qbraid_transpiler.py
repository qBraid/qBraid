from qbraid.circuits import Circuit
from qbraid import circuit_wrapper
from qbraid.circuits import Parameter


def create_circuit():
    theta = Parameter('theta')

    circ = Circuit(3)
    circ.add_instruction('H', 0)
    circ.add_instruction('H', 1)
    circ.add_instruction('H', 2)
    circ.add_instruction('CX', [0, 1])
    circ.add_instruction('RX', theta, 0)
    circ.add_instruction('RX', 3.14, 2)

    return circ
    # from qiskit import QuantumCircuit
    # qc = QuantumCircuit(2)
    # return qc.h(range(2))


if __name__ == "__main__":
    circ = create_circuit()
    print(circ)

    qbraid_circ = circuit_wrapper(circ)
    out = qbraid_circ.transpile('qiskit')
    print(out)
