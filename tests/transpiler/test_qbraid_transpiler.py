from qbraid.circuits import Circuit
from qbraid import circuit_wrapper

def create_circuit():

    circ = Circuit(3)
    circ.add_instruction('H',[],[0])
    circ.add_instruction('H',[],[1])
    circ.add_instruction('H',[],[2])
    circ.add_instruction('CX',[],[0,1])
    circ.add_instruction('RX',[3.14],[0])
    circ.add_instruction('RX',[1],[2])
    
    return circ
    # from qiskit import QuantumCircuit
    # qc = QuantumCircuit(2)
    # return qc.h(range(2))

if __name__ == "__main__":

    circ = create_circuit()

    qbraid_circ = circuit_wrapper(circ)
    out = qbraid_circ.transpile('cirq')
    print(out)
