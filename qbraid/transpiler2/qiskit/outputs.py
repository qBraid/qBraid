from qiskit import QuantumCircuit, ClassicalRegister

def circuit_to_qiskit(self, auto_measure=False) -> QuantumCircuit:

        qreg = self.qubitset.transpile("qiskit")

        if self.num_clbits:
            creg = self.clbitset.transpile("qiskit")
            # creg = QiskitClassicalRegister(self.num_clbits)
            output_circ = QuantumCircuit(qreg, creg, name="qBraid_transpiler_output")
        elif auto_measure:
            creg = ClassicalRegister(self.num_qubits)
            output_circ = QuantumCircuit(qreg, creg, name="qBraid_transpiler_output")
        else:
            output_circ = QuantumCircuit(qreg, name="qBraid_transpiler_output")

        # add instructions
        for instruction in self.instructions:
            # assert np.log2(len(instruction.gate.matrix)) == len(instruction.qubits)
            output_circ.append(*instruction.transpile("qiskit"))

        # auto measure
        if auto_measure:
            raise NotImplementedError

        return output_circ
    
def instruction_to_qiskit():
    
    raise NotImplementedError