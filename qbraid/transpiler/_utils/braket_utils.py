from typing import Union
import numpy as np
from braket.circuits import Circuit
from braket.circuits import Gate as BraketGate
from braket.circuits import Instruction, Qubit
from braket.circuits.gates import (
    CY,
    CZ,
    XX,
    XY,
    YY,
    ZZ,
    CCNot,
    CNot,
    CPhaseShift,
    H,
    I,
    ISwap,
    PhaseShift,
    PSwap,
    Rx,
    Ry,
    Rz,
    S,
    Si,
    Swap,
    T,
    Ti,
    Unitary,
    V,
    Vi,
    X,
    Y,
    Z,
)

from qbraid.transpiler.parameter import ParamID

from ..exceptions import TranspilerError

braket_gates = {
    # one-qubit, zero parameter
    "H": H,
    "X": X,
    "Y": Y,
    "Z": Z,
    "S": S,
    "Sdg": Si,
    "T": T,
    "Tdg": Ti,
    "I": I,
    "SX": V,
    "SXdg": Vi,
    # one-qubit, one parameter
    "Phase": PhaseShift,
    "RX": Rx,
    "RY": Ry,
    "RZ": Rz,
    "U1": PhaseShift,
    # two-qubit, zero parameter
    # 'CH':BraketGate.,
    "CX": CNot,
    "Swap": Swap,
    "iSwap": ISwap,
    # 'CSX':BraketGate.,
    # 'DCX': BraketGate.,
    "CY": CY,
    "CZ": CZ,
    # two-qubit, one parameter
    "RXX": XX,
    "RXY": XY,
    "RYY": YY,
    "RZZ": ZZ,
    "pSwap": PSwap,
    "CPhase": CPhaseShift,
    # multi-qubit
    "CCX": CCNot,
    # unitary
    "Unitary": Unitary,
}


def get_braket_gate_data(gate: BraketGate):
    data = {
        "type": None,
        "params": [],
        "matrix": gate.to_matrix(),
    }

    # single qubit , no parameters
    if isinstance(gate, H):
        data["type"] = "H"
    elif isinstance(gate, X):
        data["type"] = "X"
    elif isinstance(gate, Y):
        data["type"] = "Y"
    elif isinstance(gate, Z):
        data["type"] = "Z"
    elif isinstance(gate, S):
        data["type"] = "S"
    elif isinstance(gate, Si):
        data["type"] = "Sdg"
    elif isinstance(gate, T):
        data["type"] = "T"
    elif isinstance(gate, Ti):
        data["type"] = "Tdg"
    elif isinstance(gate, I):
        data["type"] = "I"
    elif isinstance(gate, V):
        data["type"] = "SX"
    elif isinstance(gate, Vi):
        data["type"] = "SXdg"

    # single-qubit, one param
    elif isinstance(gate, PhaseShift):
        data["type"] = "Phase"
        data["params"] = [gate.angle]
    elif isinstance(gate, Rx):
        data["type"] = "RX"
        data["params"] = [gate.angle]
    elif isinstance(gate, Ry):
        data["type"] = "RY"
        data["params"] = [gate.angle]
    elif isinstance(gate, Rz):
        data["type"] = "RZ"
        data["params"] = [gate.angle]

    # two-qubit zero params
    elif isinstance(gate, CNot):
        data["type"] = "CX"
        data["num_controls"] = 1
        data["base_gate"] = X()
    elif isinstance(gate, Swap):
        data["type"] = "Swap"
    elif isinstance(gate, ISwap):
        data["type"] = "iSwap"
    elif isinstance(gate, PSwap):
        data["type"] = "pSwap"
    elif isinstance(gate, CY):
        data["type"] = "CY"
        data["num_controls"] = 1
        data["base_gate"] = Y()
    elif isinstance(gate, CZ):
        data["type"] = "CZ"
        data["num_controls"] = 1
        data["base_gate"] = Z()

    # two-qubit, one param
    elif isinstance(gate, XX):
        data["type"] = "RXX"
        data["params"] = [gate.angle]
    elif isinstance(gate, XY):
        data["type"] = "RXY"
        data["params"] = [gate.angle]
    elif isinstance(gate, YY):
        data["type"] = "RYY"
        data["params"] = [gate.angle]
    elif isinstance(gate, ZZ):
        data["type"] = "RZZ"
        data["params"] = [gate.angle]
    elif isinstance(gate, CPhaseShift):
        data["type"] = "CPhase"
        data["params"] = [gate.angle]
        data["num_controls"] = 1
        data["base_gate"] = PhaseShift(gate.angle)

    # multi-qubit gates
    elif isinstance(gate, CCNot):
        data["type"] = "CCX"
        data["num_controls"] = 2
        data["base_gate"] = X()

    # unitary
    elif isinstance(gate, Unitary):
        data["type"] = "Unitary"

    # error
    else:
        raise TranspilerError("Gate of type {} not supported".format(type(gate)))

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

    elif matrix is not None:
        return braket_gates["Unitary"](matrix)

    # error
    else:
        raise TranspilerError(f"Gate of type {gate_type} not supported for Braket transpile.")


def circuit_to_braket(cw, output_qubit_mapping=None):

    if cw.input_param_mapping:
        raise TranspilerError(
            "Circuit cannot be transpiled to braket\
             because it abstract parameters."
        )

    output_circ = Circuit()

    # some instructions may be null (i.e. classically controlled gates, measurement)
    # these will return None, which should not be added to the circuit

    if not output_qubit_mapping:
        output_qubit_mapping = {x: Qubit(x) for x in range(len(cw.qubits))}

    for instruction in cw.instructions:
        instr = instruction.transpile("braket", output_qubit_mapping)
        if instr:
            output_circ.add_instruction(instr)

    return output_circ


def instruction_to_braket(iw, output_qubit_mapping, output_param_mapping):

    gate = iw.gate.transpile("braket", output_param_mapping)
    mapping = [output_qubit_mapping[q] for q in iw.qubits]

    if gate == "BraketMeasure":
        return None
    elif isinstance(gate, Unitary):
        qubits = list(reversed(mapping))
    else:
        qubits = mapping
    return Instruction(gate, qubits)


def gate_to_braket(gw, output_param_mapping=None) -> Union[BraketGate, str]:
    """Create braket gate from a qbraid gate wrapper object.

    Args:
        output_param_mapping (dict):
        gw (BraketGateWrapper):

    """

    braket_params = (
        gw.params
        if not output_param_mapping
        else [output_param_mapping[p] if isinstance(p, ParamID) else p for p in gw.params]
    )

    data = {
        "type": gw.gate_type,
        "matrix": gw.matrix,
        "name": gw.name,
        "params": braket_params,
    }

    if gw.gate_type in braket_gates:
        return create_braket_gate(data)

    elif gw.gate_type == "MEASURE":
        return "BraketMeasure"

    elif gw.matrix is not None:
        data["name"] = data["type"]
        data["type"] = "Unitary"
        return create_braket_gate(data)

    else:
        raise TranspilerError(f"Gate of type {gw.gate_type} not supported.")
