from cirq import Circuit, LineQubit
from ..qbraid.instruction import QbraidInstructionWrapper
from ..qbraid.gate import QbraidGateWrapper
from cirq.ops.measure_util import measure as CirqMeasure


def circuit_to_cirq(cw, auto_measure =False, output_mapping = None):
    
    output_circ = Circuit()

    if not output_mapping:
        output_mapping = {x:LineQubit(x) for x in range(len(cw.qubits))}

    for instruction in cw.instructions:
        output_circ.append(instruction.transpile("cirq", output_mapping=output_mapping))

    # auto measure
    if auto_measure:
        raise NotImplementedError

    return output_circ

def instruction_to_cirq(iw, output_mapping):
    
    qubits = [output_mapping[x] for x in iw.qubits]
    gate = iw.gate.transpile("cirq")

    if gate == "CirqMeasure":
        return [CirqMeasure(q, key=str(q.x)) for q in qubits]
    else:
        return gate(*qubits)