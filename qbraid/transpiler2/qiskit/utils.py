from qiskit.circuit.gate import Gate
from qiskit.circuit.measure import Measure
from qiskit.extensions.unitary import UnitaryGate
from qiskit.circuit.library.standard_gates import *
from typing import Union
from qbraid.transpiler.exceptions import CircuitError


qiskit_gates = {
    "H": HGate,
    "X": XGate,
    "Y": YGate,
    "Z": ZGate,
    "S": SGate,
    "Sdg": SdgGate,
    "T": TGate,
    "Tdg": TdgGate,
    "I": IGate,
    "SX": SXGate,
    "SXdg": SXdgGate,
    "Phase": PhaseGate,
    "RX": RXGate,
    "RY": RYGate,
    "RZ": RZGate,
    "U1": U1Gate,
    "R": RGate,
    "U2": U2Gate,
    "U": UGate,
    "U3": U3Gate,
    "CH": CHGate,
    "CX": CXGate,
    "Swap": SwapGate,
    "iSwap": iSwapGate,
    "CSX": CSXGate,
    "DCX": DCXGate,
    "CY": CYGate,
    "CZ": CZGate,
    "CPhase": CPhaseGate,
    "CRX": CRXGate,
    "RXX": RXXGate,
    "CRY": CRYGate,
    "RYY": RYYGate,
    "CRZ": CRZGate,
    "RZX": RZXGate,
    "RZZ": RZZGate,
    "CU1": CU1Gate,
    "RCCX": RCCXGate,
    "RC3X": RC3XGate,
    "CCX": CCXGate,
    "Unitary": UnitaryGate,
    "MEASURE": Measure,
}

QiskitGate = Union[Measure, Gate]


def get_qiskit_gate_data(gate: QiskitGate) -> dict:

    data = {"type": None, "params": gate.params, "matrix": None, "num_controls": 0}

    # measurement
    if isinstance(gate, Measure):
        data["type"] = "MEASURE"
    else:
        try:
            data["matrix"] = gate.to_matrix()
        except TypeError:
            pass  # parameterized circuit

    # single-qubit, zero-parameter
    if isinstance(gate, HGate):
        data["type"] = "H"
    elif isinstance(gate, XGate):
        data["type"] = "X"
    elif isinstance(gate, YGate):
        data["type"] = "Y"
    elif isinstance(gate, ZGate):
        data["type"] = "Z"
    elif isinstance(gate, SGate):
        data["type"] = "S"
    elif isinstance(gate, SdgGate):
        data["type"] = "Sdg"
    elif isinstance(gate, TGate):
        data["type"] = "T"
    elif isinstance(gate, TdgGate):
        data["type"] = "Tdg"
    elif isinstance(gate, IGate):
        data["type"] = "I"
    elif isinstance(gate, SXGate):
        data["type"] = "SX"
    elif isinstance(gate, SXdgGate):
        data["type"] = "SXdg"

    # single-qubit, one-parameter
    elif isinstance(gate, PhaseGate):
        data["type"] = "Phase"
    elif isinstance(gate, RXGate):
        data["type"] = "RX"
    elif isinstance(gate, RYGate):
        data["type"] = "RY"
    elif isinstance(gate, RZGate):
        data["type"] = "RZ"
    elif isinstance(gate, U1Gate):
        data["type"] = "U1"

    # single-qubit, two-parameter
    elif isinstance(gate, RGate):
        data["type"] = "R"
    elif isinstance(gate, U2Gate):
        data["type"] = "U2"

    # single-qubit, three-parameter
    elif isinstance(gate, UGate):
        data["type"] = "U"
    elif isinstance(gate, U3Gate):
        data["type"] = "U3"

    # two-qubit, zero-parameters
    elif isinstance(gate, CHGate):
        data["type"] = "CH"
        data["num_controls"] = gate.num_ctrl_qubits
    elif isinstance(gate, CXGate):
        data["type"] = "CX"
        data["num_controls"] = gate.num_ctrl_qubits
    elif isinstance(gate, SwapGate):
        data["type"] = "Swap"
    elif isinstance(gate, iSwapGate):
        data["type"] = "iSwap"
    elif isinstance(gate, CSXGate):
        data["type"] = "CSX"
        data["num_controls"] = gate.num_ctrl_qubits
    elif isinstance(gate, DCXGate):
        data["type"] = "DCX"
    elif isinstance(gate, CYGate):
        data["type"] = "CY"
        data["num_controls"] = gate.num_ctrl_qubits
    elif isinstance(gate, CZGate):
        data["type"] = "CZ"
        data["num_controls"] = gate.num_ctrl_qubits

    # two-qubit, one-parameter
    elif isinstance(gate, CPhaseGate):
        data["type"] = "CPhase"
        data["num_controls"] = gate.num_ctrl_qubits
    elif isinstance(gate, CRXGate):
        data["type"] = "CRX"
        data["num_controls"] = gate.num_ctrl_qubits
    elif isinstance(gate, RXXGate):
        data["type"] = "RXX"
    elif isinstance(gate, CRYGate):
        data["type"] = "CRY"
        data["num_controls"] = gate.num_ctrl_qubits
    elif isinstance(gate, RYYGate):
        data["type"] = "RYY"
    elif isinstance(gate, CRZGate):
        data["type"] = "CRZ"
        data["num_controls"] = gate.num_ctrl_qubits
    elif isinstance(gate, RZXGate):
        data["type"] = "RZX"
    elif isinstance(gate, RZZGate):
        data["type"] = "RZZ"
    elif isinstance(gate, CU1Gate):
        data["type"] = "CU1"
        data["num_controls"] = gate.num_ctrl_qubits

    # two-qubit, three-parameter
    elif isinstance(gate, CU3Gate):
        data["type"] = "CU3"
        data["num_controls"] = gate.num_ctrl_qubits

    # two-qubit, four-parameter
    elif isinstance(gate, CUGate):
        data["type"] = "CU"
        data["num_controls"] = gate.num_ctrl_qubits

    # multi-qubit
    elif isinstance(gate, CCXGate):
        data["type"] = "CCX"
        data["num_controls"] = gate.num_ctrl_qubits
    elif isinstance(gate, RCCXGate):
        data["type"] = "RCCX"
    elif isinstance(gate, RC3XGate):
        data["type"] = "RC3X"
    elif isinstance(gate, CSwapGate):
        data["type"] = "CSwap"
        data["num_controls"] = gate.num_ctrl_qubits
    elif isinstance(gate, MCPhaseGate):
        data["type"] = "MCPhase"
    elif isinstance(gate, MCU1Gate):
        data["type"] = "MCU1"

    # general unitary
    elif isinstance(gate, UnitaryGate):
        data["type"] = "Unitary"

    # error
    else:
        if data["type"] != "MEASURE":
            raise CircuitError("Gate of type {} not supported".format(type(gate)))

    return data


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
        return RCCXGate()
    elif gate_type == "RC3X":
        return RC3XGate()
    elif gate_type == "CCX":
        return CCXGate()
    elif gate_type == "MCXGrayCode":
        return MCXGrayCode(params[0])
    elif gate_type == "MCXRecursive":
        return MCXRecursive(params[0])
    elif gate_type == "MCXVChain":
        return MCXVChain(params[0])
    elif gate_type == "CSwap":
        return CSwapGate()

    # multi-qubit, one-parameter
    elif gate_type == "MCU1":
        return MCU1Gate(params[0], params[1])
    elif gate_type == "MCPhase":
        return MCPhaseGate(params[0], params[1])

    # non-compatible types, go from matrix
    elif not (matrix is None):
        return UnitaryGate(matrix, label=gate_type)

    else:
        raise CircuitError("{} gate not supported for Qiskit conversion.".format(gate_type))
