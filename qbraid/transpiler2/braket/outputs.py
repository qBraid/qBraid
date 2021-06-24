from braket import Circuit
from braket import Instruction

def circuit_to_braket(circuitwrapper):

    output_circ = Circuit()

    # some instructions may be null (i.e. classically controlled gates, measurement)
    # these will return None, which should not be added to the circuit
    for instruction in circuitwrapper.instructions:
        instr = instruction.transpile("braket")
        if instr:
            output_circ.add_instruction(instr)

    return output_circ

def instruction_to_braket(iw, output_mapping):
    
    gate = iw.gate.transpile("braket")
    qubits = [output_mapping[q] for q in iw.qubits]
    
    if gate == "BraketMeasure":
        return None
    else:
        return Instruction(gate, qubits)