from braket import Circuit

def to_braket(circuitwrapper):

    output_circ = Circuit()

    # some instructions may be null (i.e. classically controlled gates, measurement)
    # these will return None, which should not be added to the circuit
    for instruction in circuitwrapper.instructions:
        instr = instruction.transpile("braket")
        if instr:
            output_circ.add_instruction(instr)

    return output_circ