from qbraid.exceptions import PackageError
from braket.circuits import Circuit
from braket.circuits import Instruction
from braket.circuits import Qubit
from braket.circuits import Gate as BraketGate

from .utils import create_braket_gate, braket_gates


def circuit_to_braket(cw, output_mapping=None):

    output_circ = Circuit()

    # some instructions may be null (i.e. classically controlled gates, measurement)
    # these will return None, which should not be added to the circuit

    if not output_mapping:
        output_mapping = {x: Qubit(x) for x in range(len(cw.qubits))}

    for instruction in cw.instructions:
        instr = instruction.transpile("braket", output_mapping)
        if instr:
            output_circ.add_instruction(instr)

    return output_circ


def instruction_to_braket(iw, output_qubit_mapping, output_param_mapping):

    gate = iw.gate.transpile("braket", output_param_mapping)
    qubits = [output_qubit_mapping[q] for q in iw.qubits]

    if gate == "BraketMeasure":
        return None
    else:
        return Instruction(gate, qubits)


def gate_to_braket(gw, output_param_mapping) -> BraketGate:

    """Create braket gate from a qbraid gate wrapper object."""

    # braket_params = [output_param_mapping[p] if isinstance(p,ParamID) else p for p in gw.params]

    if gw._gate_type in braket_gates.keys():
        return create_braket_gate(gw._gate_type, gw.params)
    elif gw._gate_type == "MEASURE":
        return "BraketMeasure"
    else:
        raise PackageError("Gate type not supported.")
