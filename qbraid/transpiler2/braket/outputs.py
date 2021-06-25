from braket.circuits import Circuit
from braket.circuits import Instruction
from braket.circuits import Qubit

def circuit_to_braket(cw, output_mapping = None):

    output_circ = Circuit()

    # some instructions may be null (i.e. classically controlled gates, measurement)
    # these will return None, which should not be added to the circuit

    if not output_mapping:
        output_mapping = {x:Qubit(x) for x in range(len(cw.qubits))}


    for instruction in cw.instructions:
        instr = instruction.transpile("braket", output_mapping)
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