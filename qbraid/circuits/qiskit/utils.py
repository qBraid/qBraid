from qiskit.circuit.gate import Gate
from qiskit.circuit.measure import Measure
from qiskit.extensions.unitary import UnitaryGate
from qiskit.circuit.exceptions import CircuitError
from qbraid.circuits.gate import GateError
from typing import Union

QiskitGate = Union[Measure, Gate]


def get_qiskit_gate_data(gate: QiskitGate) -> dict:
    """

    :param gate:
    :return:
    """

    data = {"type": None, "params": gate.params, "matrix": None, "num_controls": 0}
    try:
        data["matrix"] = gate.to_matrix()
    except CircuitError as e:
        raise GateError("Unable to extract matrix represention from {}".format(type(gate))) from e

    # measurement
    if isinstance(gate, Measure):
        data["type"] = "MEASURE"

    # single-qubit, zero-parameter
    elif isinstance(gate, Gate.HGate):
        data["type"] = "H"
    elif isinstance(gate, Gate.XGate):
        data["type"] = "X"
    elif isinstance(gate, Gate.YGate):
        data["type"] = "Y"
    elif isinstance(gate, Gate.ZGate):
        data["type"] = "Z"
    elif isinstance(gate, Gate.SGate):
        data["type"] = "S"
    elif isinstance(gate, Gate.SdgGate):
        data["type"] = "Sdg"
    elif isinstance(gate, Gate.TGate):
        data["type"] = "T"
    elif isinstance(gate, Gate.TdgGate):
        data["type"] = "Tdg"
    elif isinstance(gate, Gate.IGate):
        data["type"] = "I"
    elif isinstance(gate, Gate.SXGate):
        data["type"] = "SX"
    elif isinstance(gate, Gate.SXdgGate):
        data["type"] = "SXdg"

    # single-qubit, one-parameter
    elif isinstance(gate, Gate.PhaseGate):
        data["type"] = "Phase"
        data["params"] = gate.params
    elif isinstance(gate, Gate.RXGate):
        data["type"] = "RX"
        data["params"] = gate.params
    elif isinstance(gate, Gate.RYGate):
        data["type"] = "RY"
        data["params"] = gate.params
    elif isinstance(gate, Gate.RZGate):
        data["type"] = "RZ"
        data["params"] = gate.params
    elif isinstance(gate, Gate.U1Gate):
        data["type"] = "U1"
        data["params"] = gate.params

    # single-qubit, two-parameter
    elif isinstance(gate, Gate.RGate):
        data["type"] = "R"
        data["params"] = gate.params
    elif isinstance(gate, Gate.U2Gate):
        data["type"] = "U2"
        data["params"] = gate.params

    # single-qubit, three-parameter
    elif isinstance(gate, Gate.UGate):
        data["type"] = "U"
        data["params"] = gate.params
    elif isinstance(gate, Gate.U3Gate):
        data["type"] = "U3"
        data["params"] = gate.params

    # two-qubit, zero-parameters
    elif isinstance(gate, Gate.CHGate):
        data["type"] = "CH"
        data["num_controls"] = gate.num_ctrl_qubits
    elif isinstance(gate, Gate.CXGate):
        data["type"] = "CX"
        data["num_controls"] = gate.num_ctrl_qubits
    elif isinstance(gate, Gate.SwapGate):
        data["type"] = "Swap"
    elif isinstance(gate, Gate.iSwapGate):
        data["type"] = "iSwap"
    elif isinstance(gate, Gate.CSXGate):
        data["type"] = "CSX"
        data["num_controls"] = gate.num_ctrl_qubits
    elif isinstance(gate, Gate.DCXGate):
        data["type"] = "DCX"
    elif isinstance(gate, Gate.CYGate):
        data["type"] = "CY"
        data["num_controls"] = gate.num_ctrl_qubits
    elif isinstance(gate, Gate.CZGate):
        data["type"] = "CZ"
        data["num_controls"] = gate.num_ctrl_qubits

    # two-qubit, one-parameter
    elif isinstance(gate, Gate.CPhaseGate):
        data["type"] = "CPhase"
        data["params"] = gate.params
        data["num_controls"] = gate.num_ctrl_qubits
    elif isinstance(gate, Gate.CRXGate):
        data["type"] = "CRX"
        data["params"] = gate.params
        data["num_controls"] = gate.num_ctrl_qubits
    elif isinstance(gate, Gate.RXXGate):
        data["type"] = "RXX"
        data["params"] = gate.params
    elif isinstance(gate, Gate.CRYGate):
        data["type"] = "CRY"
        data["params"] = gate.params
        data["num_controls"] = gate.num_ctrl_qubits
    elif isinstance(gate, Gate.RYYGate):
        data["type"] = "RYY"
        data["params"] = gate.params
    elif isinstance(gate, Gate.CRZGate):
        data["type"] = "CRZ"
        data["params"] = gate.params
        data["num_controls"] = gate.num_ctrl_qubits
    elif isinstance(gate, Gate.RZXGate):
        data["type"] = "RZX"
        data["params"] = gate.params
    elif isinstance(gate, Gate.RZZGate):
        data["type"] = "RZZ"
        data["params"] = gate.params
    elif isinstance(gate, Gate.CU1Gate):
        data["type"] = "CU1"
        data["params"] = gate.params
        data["num_controls"] = gate.num_ctrl_qubits

    # two-qubit, three-parameter
    elif isinstance(gate, Gate.CU3Gate):
        data["type"] = "CU3"
        data["params"] = gate.params
        data["num_controls"] = gate.num_ctrl_qubits

    # two-qubit, four-parameter
    elif isinstance(gate, Gate.CUGate):
        data["type"] = "CU"
        data["params"] = gate.params
        data["num_controls"] = gate.num_ctrl_qubits

    # multi-qubit
    elif isinstance(gate, Gate.CCXGate):
        data["type"] = "CCX"
        data["num_controls"] = gate.num_ctrl_qubits
    elif isinstance(gate, Gate.RCCXGate):
        data["type"] = "RCCX"
    elif isinstance(gate, Gate.RC3XGate):
        data["type"] = "RC3X"
    elif isinstance(gate, Gate.CSwapGate):
        data["type"] = "CSwap"
        data["num_controls"] = gate.num_ctrl_qubits
    elif isinstance(gate, Gate.MCPhaseGate):
        data["type"] = "MCPhase"
    elif isinstance(gate, Gate.MCU1Gate):
        data["type"] = "MCU1"

    # general unitary
    elif isinstance(gate, UnitaryGate):
        data["type"] = "Unitary"

    # error
    else:
        raise GateError("Gate of type {} not supported".format(type(gate)))

    return data


qiskit_gates = {
    "H": Gate.HGate,
    "X": Gate.XGate,
    "Y": Gate.YGate,
    "Z": Gate.ZGate,
    "S": Gate.SGate,
    "Sdg": Gate.SdgGate,
    "T": Gate.TGate,
    "Tdg": Gate.TdgGate,
    "I": Gate.IGate,
    "SX": Gate.SXGate,
    "SXdg": Gate.SXdgGate,
    "Phase": Gate.PhaseGate,
    "RX": Gate.RXGate,
    "RY": Gate.RYGate,
    "RZ": Gate.RZGate,
    "U1": Gate.U1Gate,
    "R": Gate.RGate,
    "U2": Gate.U2Gate,
    "U": Gate.UGate,
    "U3": Gate.U3Gate,
    "CH": Gate.CHGate,
    "CX": Gate.CXGate,
    "Swap": Gate.SwapGate,
    "iSwap": Gate.iSwapGate,
    "CSX": Gate.CSXGate,
    "DCX": Gate.DCXGate,
    "CY": Gate.CYGate,
    "CZ": Gate.CZGate,
    "CPhase": Gate.CPhaseGate,
    "CRX": Gate.CRXGate,
    "RXX": Gate.RXXGate,
    "CRY": Gate.CRYGate,
    "RYY": Gate.RYYGate,
    "CRZ": Gate.CRZGate,
    "RZX": Gate.RZXGate,
    "RZZ": Gate.RZZGate,
    "CU1": Gate.CU1Gate,
    "RCCX": Gate.RCCXGate,
    "RC3X": Gate.RC3XGate,
    "CCX": Gate.CCXGate,
    "MEASURE": Measure,
    "Unitary": UnitaryGate,
}


def create_qiskit_gate(data: dict) -> QiskitGate:
    """

    :param data:
    :return:
    """

    gate_type = data["type"]
    params = data["params"]
    matrix = data["matrix"]

    # measure
    if gate_type == "MEASURE":
        return qiskit_gates[gate_type]()

    # single-qubit, zero-parameter
    elif gate_type in ("H", "X", "Y", "Z", "S", "Sdg", "T", "Tdg", "I", "SX", "SXdg"):
        return qiskit_gates[gate_type]()

    # single-qubit, one-parameter
    elif gate_type in ("Phase", "RX", "RY", "RZ", "U1"):
        return qiskit_gates[gate_type](params[0])

    # single-qubit, two-parameter
    if gate_type in ("R", "U2"):
        return qiskit_gates[gate_type](params[0], params[1])

    # single-qubit, three-parameter
    elif gate_type in ("U", "U3"):
        return qiskit_gates[gate_type]()

    # two-qubit, zero-parameter
    elif gate_type in ("CH", "CX", "Swap", "iSwap", "CSX", "DCX", "CY", "CZ"):
        return qiskit_gates[gate_type]()

    # two-qubit, one-parameter
    elif gate_type in ("CPhase", "CRX", "RXX", "CRY", "RYY", "CRZ", "RZX", "RZZ", "CU1"):
        return qiskit_gates[gate_type](params[0])

    # two-qubit, three-parameter
    elif gate_type == "CU3":
        return qiskit_gates[gate_type]()

    # four-parameter
    elif gate_type == "CU":
        return qiskit_gates[gate_type]()

    # multi-qubit, zero-parameter
    elif gate_type == "RCCX":
        return Gate.RCCXGate()
    elif gate_type == "RC3X":
        return Gate.RC3XGate()
    elif gate_type == "CCX":
        return Gate.CCXGate()
    elif gate_type == "MCXGrayCode":
        return Gate.MCXGrayCodeGate()
    elif gate_type == "MCXRecursive":
        return Gate.MCXRecursiveGate()
    elif gate_type == "MCXVChain":
        return Gate.MCXVChainGate()
    elif gate_type == "CSwap":
        return Gate.CSwapGate()

    # multi-qubit, one-parameter
    elif gate_type == "MCU1":
        return Gate.MCU1Gate()
    elif gate_type == "MCPhase":
        return Gate.MCPhaseGate()

    # non-compatible types, go from matrix
    elif not (matrix is None):
        return UnitaryGate(matrix, label=gate_type)

    else:
        raise GateError("{} gate not supported".format(gate_type))
