from cirq import Circuit
from ..clbit import Clbit
from ..qbraid.instruction import QbraidInstructionWrapper
from ..qbraid.gate import QbraidGateWrapper

def circuit_to_cirq(cw, auto_measure =False):
    
    output_circ = Circuit()

    for instruction in cw.instructions:
        output_circ.append(instruction.transpile("cirq"))

    # auto measure
    if auto_measure:
        for index, qubit in enumerate(cw.qubitset.qubits):
            clbit = Clbit(index)
            instruction = QbraidInstructionWrapper(
                QbraidGateWrapper(gate_type="MEASURE"), [qubit], [clbit]
            )
            output_circ.append(instruction.transpile("cirq"))

    return output_circ

def instruction_to_cirq():
    pass