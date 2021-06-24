from qiskit import QuantumCircuit, ClassicalRegister, QuantumRegister
from qiskit.circuit.measure import Measure as QiskitMeasure
from qiskit.circuit.quantumregister import Qubit

def circuit_to_qiskit(cw, auto_measure=False, output_mapping = None) -> QuantumCircuit:

    
        qreg = QuantumRegister(cw.num_qubits)
        output_mapping = {index:Qubit(qreg,index) for index in range(len(qreg))}
        
        #get instruction data to intermediate format 
        #(will eventually include combing through moments)
        data = []
        measurement_qubit_indices = set()
        for instruction in cw.instructions:
            gate, qubits, measurement_qubits = instruction.transpile('qiskit', output_mapping)
            data.append((gate,qubits, measurement_qubits))
            measurement_qubit_indices.update(measurement_qubits)
        
        #determine the length of the classical register and initialize
        if auto_measure:
            creg = ClassicalRegister(len(cw.num_qubits))
        elif len(measurement_qubit_indices) == 0:
            creg = None
        else: 
            creg = ClassicalRegister(len(measurement_qubit_indices))
            #store how a qubit id maps to a clbit for the user
            clbit_mapping = {qubit:index for index,qubit in enumerate(measurement_qubit_indices)}
        
        if creg:
            output_circ = QuantumCircuit( qreg, creg, name = "qBraid_transpiler_output")
        else: 
            output_circ = QuantumCircuit( qreg, name = "qBraid_transpiler_output")

        # add instructions to circuit
        for gate, qubits, measurement_qubits in data:
            clbits = None if not measurement_qubits else [clbit_mapping[q] for q in measurement_qubits]
            output_circ.append(gate, qubits, clbits)

        # auto measure
        if auto_measure:
            raise NotImplementedError

        return output_circ
    
def instruction_to_qiskit(iw, output_mapping):

    gate = iw.gate.transpile("qiskit")
    qubits = [output_mapping[q] for q in iw.qubits]


    if isinstance(gate, QiskitMeasure):
        return gate, qubits, iw.qubits
    else:
        return gate, qubits, []