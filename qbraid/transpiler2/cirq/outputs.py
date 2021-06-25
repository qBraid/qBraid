from cirq import Circuit, LineQubit
from cirq.ops.measure_util import measure as CirqMeasure


def circuit_to_cirq(cw, 
    auto_measure =False, 
    output_qubit_mapping = None,
    output_param_mapping = None):
    
    output_circ = Circuit()

    if not output_qubit_mapping:
        output_qubit_mapping = {x:LineQubit(x) for x in range(len(cw.qubits))}

    for instruction in cw.instructions:
        output_circ.append(instruction.transpile(
            "cirq", 
            output_qubit_mapping=output_qubit_mapping)
        )

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