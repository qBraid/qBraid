from braket.circuits import Circuit
from braket.circuits import Gate as BraketGate
from braket.circuits import Instruction
from braket.circuits import Qubit
from typing import Union

from qbraid.transpiler.parameter import ParamID

braket_gates = {
    # one-qubit, zero parameter
    "H": BraketGate.H,
    "X": BraketGate.X,
    "Y": BraketGate.Y,
    "Z": BraketGate.Z,
    "S": BraketGate.S,
    "Sdg": BraketGate.Si,
    "T": BraketGate.T,
    "Tdg": BraketGate.Ti,
    "I": BraketGate.I,
    "SX": BraketGate.V,
    "SXdg": BraketGate.Vi,
    # one-qubit, one parameter
    "Phase": BraketGate.PhaseShift,
    "RX": BraketGate.Rx,
    "RY": BraketGate.Ry,
    "RZ": BraketGate.Rz,
    "U1": BraketGate.PhaseShift,
    # two-qubit, zero parameter
    # 'CH':BraketGate.,
    "CX": BraketGate.CNot,
    "Swap": BraketGate.Swap,
    "iSwap": BraketGate.ISwap,
    "pSwap": BraketGate.PSwap,
    # 'CSX':BraketGate.,
    # 'DCX': BraketGate.,
    "CY": BraketGate.CY,
    "CZ": BraketGate.CZ,
    # two-qubit, one parameter
    "RXX": BraketGate.XX,
    "RXY": BraketGate.XY,
    "RYY": BraketGate.YY,
    "RZZ": BraketGate.ZZ,
    "CPhase": BraketGate.CPhaseShift,
    # multi-qubit
    "CCX": BraketGate.CCNot,
    # unitary
    "Unitary": BraketGate.Unitary,
}


def get_braket_gate_data(gate: BraketGate):
    data = {
        "type": None,
        "params": [],
        "matrix": gate.to_matrix(),
    }

    # single qubit , no parameters
    if isinstance(gate, BraketGate.H):
        data["type"] = "H"
    elif isinstance(gate, BraketGate.X):
        data["type"] = "X"
    elif isinstance(gate, BraketGate.Y):
        data["type"] = "Y"
    elif isinstance(gate, BraketGate.Z):
        data["type"] = "Z"
    elif isinstance(gate, BraketGate.S):
        data["type"] = "S"
    elif isinstance(gate, BraketGate.Si):
        data["type"] = "Sdg"
    elif isinstance(gate, BraketGate.T):
        data["type"] = "T"
    elif isinstance(gate, BraketGate.Ti):
        data["type"] = "Tdg"
    elif isinstance(gate, BraketGate.I):
        data["type"] = "I"
    elif isinstance(gate, BraketGate.V):
        data["type"] = "SX"
    elif isinstance(gate, BraketGate.Vi):
        data["type"] = "SXdg"

    # single-qubit, one param
    elif isinstance(gate, BraketGate.PhaseShift):
        data["type"] = "Phase"
        data["params"] = [gate.angle]
    elif isinstance(gate, BraketGate.Rx):
        data["type"] = "RX"
        data["params"] = [gate.angle]
    elif isinstance(gate, BraketGate.Ry):
        data["type"] = "RY"
        data["params"] = [gate.angle]
    elif isinstance(gate, BraketGate.Rz):
        data["type"] = "RZ"
        data["params"] = [gate.angle]

    # two-qubit zero params
    elif isinstance(gate, BraketGate.CNot):
        data["type"] = "CX"
        data["num_controls"] = 1
        data["base_gate"] = BraketGate.X()
    elif isinstance(gate, BraketGate.Swap):
        data["type"] = "Swap"
    elif isinstance(gate, BraketGate.ISwap):
        data["type"] = "iSwap"
    elif isinstance(gate, BraketGate.PSwap):
        data["type"] = "pSwap"
    elif isinstance(gate, BraketGate.CY):
        data["type"] = "CY"
        data["num_controls"] = 1
        data["base_gate"] = BraketGate.Y()
    elif isinstance(gate, BraketGate.CZ):
        data["type"] = "CZ"
        data["num_controls"] = 1
        data["base_gate"] = BraketGate.Z()

    # two-qubit, one param
    elif isinstance(gate, BraketGate.XX):
        data["type"] = "RXX"
        data["params"] = [gate.angle]
    elif isinstance(gate, BraketGate.XY):
        data["type"] = "RXY"
        data["params"] = [gate.angle]
    elif isinstance(gate, BraketGate.YY):
        data["type"] = "RYY"
        data["params"] = [gate.angle]
    elif isinstance(gate, BraketGate.ZZ):
        data["type"] = "RZZ"
        data["params"] = [gate.angle]
    elif isinstance(gate, BraketGate.CPhaseShift):
        data["type"] = "CPhase"
        data["params"] = [gate.angle]
        data["num_controls"] = 1
        data["base_gate"] = BraketGate.PhaseShift(gate.angle)

    # multi-qubit gates
    elif isinstance(gate, BraketGate.CCNot):
        data["type"] = "CCX"
        data["num_controls"] = 2
        data["base_gate"] = BraketGate.X()

    # unitary
    elif isinstance(gate, BraketGate.Unitary):
        data["type"] = "Unitary"

    # error
    else:
        raise TypeError("Gate of type {} not supported".format(type(gate)))

    return data


def create_braket_gate(data):

    gate_type = data["type"]
    params = data["params"]
    matrix = data["matrix"]

    # single qubit
    if gate_type in ("H", "X", "Y", "Z", "S", "Sdg", "T", "Tdg", "I", "SX", "SXdg"):
        return braket_gates[gate_type]()

    elif gate_type in ("Phase", "RX", "RY", "RZ", "U1"):
        return braket_gates[gate_type](params[0])

    # two-qubit, zero-params
    elif gate_type in ("CX", "Swap", "iSwap", "CY", "CZ"):
        return braket_gates[gate_type]()

    # two-qubit, one-param
    elif gate_type in ("RXX", "RXY", "RYY", "RZZ", "CPhase"):
        # choice of CPhaseShift, CPhaseShift00, CPhaseShift01, CPhaseShift10
        return braket_gates[gate_type](params[0])

    # multi-qubit gates
    elif gate_type in "CCX":
        return braket_gates[gate_type]()

    # measure
    elif gate_type == "MEASURE":
        return "BraketMeasure"

    elif not (matrix is None):
        return braket_gates["Unitary"](matrix)

    # error
    else:
        raise TypeError(f"Gate of type {gate_type} not supported for Braket transpile.")


def circuit_to_braket(cw, output_mapping=None):

    output_circ = Circuit()  # create circuit object

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


def gate_to_braket(gw, output_param_mapping=None) -> Union[BraketGate, str]:
    """Create braket gate from a qbraid gate wrapper object.

    Args:
        output_param_mapping (dict):
        gw (BraketGateWrapper):

    """

    braket_params = gw.params if not output_param_mapping \
        else [output_param_mapping[p] if isinstance(p, ParamID) else p for p in gw.params]

    data = {
        "type": gw._gate_type,
        "matrix": gw.matrix,
        "name": gw.name,
        "params": braket_params,
    }

    if gw._gate_type in braket_gates.keys():
        return create_braket_gate(data)

    elif gw._gate_type == "MEASURE":
        return "BraketMeasure"

    elif gw.matrix is not None:
        data["name"] = data["type"]
        data["type"] = "Unitary"
        return create_braket_gate(data)

    else:
        raise TypeError(f"Gate of type {gw._gate_type} not supported.")
