from qiskit.circuit.gate import Gate
from qiskit.circuit.measure import Measure
from qiskit.extensions.unitary import UnitaryGate
from qiskit.circuit.library.standard_gates import *
from typing import Union
from qbraid.circuits.exceptions import CircuitError


QiskitGate = Union[Measure, Gate]


def get_qiskit_gate_data(gate: QiskitGate) -> dict:
    """

    :param gate:
    :return:
    """
    data = {
        "type": None,
        "params": gate.params,
        "matrix": gate.to_matrix(),
        "num_controls": 0
    }

    # measurement
    if isinstance(gate, Measure):
        data["type"] = "MEASURE"

    # single-qubit, zero-parameter
    elif isinstance(gate, h.HGate):
        data["type"] = "H"
    elif isinstance(gate, x.XGate):
        data["type"] = "X"
    elif isinstance(gate, y.YGate):
        data["type"] = "Y"
    elif isinstance(gate, z.ZGate):
        data["type"] = "Z"
    elif isinstance(gate, s.SGate):
        data["type"] = "S"
    elif isinstance(gate, s.SdgGate):
        data["type"] = "Sdg"
    elif isinstance(gate, t.TGate):
        data["type"] = "T"
    elif isinstance(gate, t.TdgGate):
        data["type"] = "Tdg"
    elif isinstance(gate, i.IGate):
        data["type"] = "I"
    elif isinstance(gate, sx.SXGate):
        data["type"] = "SX"
    elif isinstance(gate, sx.SXdgGate):
        data["type"] = "SXdg"

    # single-qubit, one-parameter
    elif isinstance(gate, p.PhaseGate):
        data["type"] = "Phase"
        data["params"] = gate.params
    elif isinstance(gate, rx.RXGate):
        data["type"] = "RX"
        data["params"] = gate.params
    elif isinstance(gate, ry.RYGate):
        data["type"] = "RY"
        data["params"] = gate.params
    elif isinstance(gate, rz.RZGate):
        data["type"] = "RZ"
        data["params"] = gate.params
    elif isinstance(gate, u1.U1Gate):
        data["type"] = "U1"
        data["params"] = gate.params

    # single-qubit, two-parameter
    elif isinstance(gate, r.RGate):
        data["type"] = "R"
        data["params"] = gate.params
    elif isinstance(gate, u2.U2Gate):
        data["type"] = "U2"
        data["params"] = gate.params

    # single-qubit, three-parameter
    elif isinstance(gate, u.UGate):
        data["type"] = "U"
        data["params"] = gate.params
    elif isinstance(gate, u3.U3Gate):
        data["type"] = "U3"
        data["params"] = gate.params

    # two-qubit, zero-parameters
    elif isinstance(gate, h.CHGate):
        data["type"] = "CH"
        data["num_controls"] = gate.num_ctrl_qubits
    elif isinstance(gate, x.CXGate):
        data["type"] = "CX"
        data["num_controls"] = gate.num_ctrl_qubits
    elif isinstance(gate, swap.SwapGate):
        data["type"] = "Swap"
    elif isinstance(gate, iswap.iSwapGate):
        data["type"] = "iSwap"
    elif isinstance(gate, sx.CSXGate):
        data["type"] = "CSX"
        data["num_controls"] = gate.num_ctrl_qubits
    elif isinstance(gate, dcx.DCXGate):
        data["type"] = "DCX"
    elif isinstance(gate, y.CYGate):
        data["type"] = "CY"
        data["num_controls"] = gate.num_ctrl_qubits
    elif isinstance(gate, z.CZGate):
        data["type"] = "CZ"
        data["num_controls"] = gate.num_ctrl_qubits

    # two-qubit, one-parameter
    elif isinstance(gate, p.CPhaseGate):
        data["type"] = "CPhase"
        data["params"] = gate.params
        data["num_controls"] = gate.num_ctrl_qubits
    elif isinstance(gate, rx.CRXGate):
        data["type"] = "CRX"
        data["params"] = gate.params
        data["num_controls"] = gate.num_ctrl_qubits
    elif isinstance(gate, rxx.RXXGate):
        data["type"] = "RXX"
        data["params"] = gate.params
    elif isinstance(gate, ry.CRYGate):
        data["type"] = "CRY"
        data["params"] = gate.params
        data["num_controls"] = gate.num_ctrl_qubits
    elif isinstance(gate, ryy.RYYGate):
        data["type"] = "RYY"
        data["params"] = gate.params
    elif isinstance(gate, rz.CRZGate):
        data["type"] = "CRZ"
        data["params"] = gate.params
        data["num_controls"] = gate.num_ctrl_qubits
    elif isinstance(gate, rzx.RZXGate):
        data["type"] = "RZX"
        data["params"] = gate.params
    elif isinstance(gate, rzz.RZZGate):
        data["type"] = "RZZ"
        data["params"] = gate.params
    elif isinstance(gate, u1.CU1Gate):
        data["type"] = "CU1"
        data["params"] = gate.params
        data["num_controls"] = gate.num_ctrl_qubits

    # two-qubit, three-parameter
    elif isinstance(gate, u3.CU3Gate):
        data["type"] = "CU3"
        data["params"] = gate.params
        data["num_controls"] = gate.num_ctrl_qubits

    # two-qubit, four-parameter
    elif isinstance(gate, u.CUGate):
        data["type"] = "CU"
        data["params"] = gate.params
        data["num_controls"] = gate.num_ctrl_qubits

    # multi-qubit
    elif isinstance(gate, x.CCXGate):
        data["type"] = "CCX"
        data["num_controls"] = gate.num_ctrl_qubits
    elif isinstance(gate, x.RCCXGate):
        data["type"] = "RCCX"
    elif isinstance(gate, x.RC3XGate):
        data["type"] = "RC3X"
    elif isinstance(gate, swap.CSwapGate):
        data["type"] = "CSwap"
        data["num_controls"] = gate.num_ctrl_qubits
    elif isinstance(gate, p.MCPhaseGate):
        data["type"] = "MCPhase"
    elif isinstance(gate, u1.MCU1Gate):
        data["type"] = "MCU1"

    # general unitary
    elif isinstance(gate, UnitaryGate):
        data["type"] = "Unitary"

    # error
    else:
        raise CircuitError("Gate of type {} not supported".format(type(gate)))

    return data


qiskit_gates = {
    "H": h.HGate,
    "X": x.XGate,
    "Y": y.YGate,
    "Z": z.ZGate,
    "S": s.SGate,
    "Sdg": s.SdgGate,
    "T": t.TGate,
    "Tdg": t.TdgGate,
    "I": i.IGate,
    "SX": sx.SXGate,
    "SXdg": sx.SXdgGate,
    "Phase": p.PhaseGate,
    "RX": rx.RXGate,
    "RY": ry.RYGate,
    "RZ": rz.RZGate,
    "U1": u1.U1Gate,
    "R": r.RGate,
    "U2": u2.U2Gate,
    "U": u.UGate,
    "U3": u3.U3Gate,
    "CH": h.CHGate,
    "CX": x.CXGate,
    "Swap": swap.SwapGate,
    "iSwap": iswap.iSwapGate,
    "CSX": sx.CSXGate,
    "DCX": dcx.DCXGate,
    "CY": y.CYGate,
    "CZ": z.CZGate,
    "CPhase": p.CPhaseGate,
    "CRX": rx.CRXGate,
    "RXX": rxx.RXXGate,
    "CRY": ry.CRYGate,
    "RYY": ryy.RYYGate,
    "CRZ": rz.CRZGate,
    "RZX": rzx.RZXGate,
    "RZZ": rzz.RZZGate,
    "CU1": u1.CU1Gate,
    "RCCX": x.RCCXGate,
    "RC3X": x.RC3XGate,
    "CCX": x.CCXGate,
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
    num_controls = data["num_controls"]

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
        return x.RCCXGate()
    elif gate_type == "RC3X":
        return x.RC3XGate()
    elif gate_type == "CCX":
        return x.CCXGate()
    elif gate_type == "MCXGrayCode":
        return x.MCXGrayCode(num_controls)
    elif gate_type == "MCXRecursive":
        return x.MCXRecursive(num_controls)
    elif gate_type == "MCXVChain":
        return x.MCXVChain(num_controls)
    elif gate_type == "CSwap":
        return swap.CSwapGate()

    # multi-qubit, one-parameter
    elif gate_type == "MCU1":
        return u1.MCU1Gate(params[0], num_controls)
    elif gate_type == "MCPhase":
        return p.MCPhaseGate(params[0], num_controls)

    # non-compatible types, go from matrix
    elif not (matrix is None):
        return UnitaryGate(matrix, label=gate_type)

    else:
        raise CircuitError("{} gate not supported for Qiskit conversion.".format(gate_type))
