from cirq import Circuit, LineQubit
from cirq.ops.measure_util import measure as CirqMeasure
from sympy import Symbol

from qbraid.transpiler.parameter import ParamID
from .utils import cirq_gates, create_cirq_gate


def circuit_to_cirq(cw, auto_measure=False, output_qubit_mapping=None, output_param_mapping=None):

    output_circ = Circuit()

    if not output_qubit_mapping:
        output_qubit_mapping = {x: LineQubit(x) for x in range(len(cw.qubits))}

    if not output_param_mapping:
        output_param_mapping = {pid: Symbol(pid.name) for pid in cw.params}

    for instruction in cw.instructions:
        output_circ.append(
            instruction.transpile(
                "cirq",
                output_qubit_mapping=output_qubit_mapping,
                output_param_mapping=output_param_mapping,
            )
        )

    # auto measure
    if auto_measure:
        raise NotImplementedError

    return output_circ


def instruction_to_cirq(iw, output_qubit_mapping, output_param_mapping):

    qubits = [output_qubit_mapping[x] for x in iw.qubits]
    gate = iw.gate.transpile("cirq", output_param_mapping)

    if gate == "CirqMeasure":
        return [CirqMeasure(q, key=str(q.x)) for q in qubits]
    else:
        return gate(*qubits)


def gate_to_cirq(gw, output_param_mapping):

    """Create cirq gate from a qbraid gate wrapper object."""

    cirq_params = [output_param_mapping[p] if isinstance(p, ParamID) else p for p in gw.params]

    data = {
        "type": gw._gate_type,
        "matrix": gw.matrix,
        "name": gw.name,
        "params": cirq_params,
    }

    if gw._gate_type in cirq_gates.keys():
        return create_cirq_gate(data)

    elif gw.base_gate:
        return gw.base_gate.transpile("cirq", output_param_mapping).controlled(gw.num_controls)

    elif not (gw.matrix is None):
        data["name"] = data["type"]
        data["type"] = "Unitary"
        return create_cirq_gate(data)

    else:
        raise TypeError(f"Gate type {gw._gate_type} not supported.")
