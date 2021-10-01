from typing import Tuple, Union
import qiskit
from qiskit import ClassicalRegister, QuantumCircuit, QuantumRegister
from qiskit.circuit import Instruction
from qiskit.circuit.gate import Gate
from qiskit.circuit.library.standard_gates import *
from qiskit.circuit.measure import Measure
from qiskit.circuit.parameter import Parameter as QiskitParameter
from qiskit.circuit.quantumregister import Qubit
from qiskit.extensions.unitary import UnitaryGate

from qbraid.transpiler.parameter import ParamID

from ..exceptions import TranspilerError

qiskit_gates = {
    "H": qiskit.circuit.library.standard_gates.h.HGate,
    "X": qiskit.circuit.library.standard_gates.x.XGate,
    "Y": qiskit.circuit.library.standard_gates.y.YGate,
    "Z": qiskit.circuit.library.standard_gates.z.ZGate,
    "S": qiskit.circuit.library.standard_gates.s.SGate,
    "Sdg": qiskit.circuit.library.standard_gates.s.SdgGate,
    "T": qiskit.circuit.library.standard_gates.t.TGate,
    "Tdg": qiskit.circuit.library.standard_gates.t.TdgGate,
    "I": qiskit.circuit.library.standard_gates.i.IGate,
    "SX": qiskit.circuit.library.standard_gates.sx.SXGate,
    "SXdg": qiskit.circuit.library.standard_gates.sx.SXdgGate,
    "Phase": qiskit.circuit.library.standard_gates.p.PhaseGate,
    "RX": qiskit.circuit.library.standard_gates.rx.RXGate,
    "RY": qiskit.circuit.library.standard_gates.ry.RYGate,
    "RZ": qiskit.circuit.library.standard_gates.rz.RZGate,
    "U1": qiskit.circuit.library.standard_gates.U1Gate,
    "R": qiskit.circuit.library.standard_gates.r.RGate,
    "U2": qiskit.circuit.library.standard_gates.u2.U2Gate,
    "U": qiskit.circuit.library.standard_gates.u.UGate,
    "U3": qiskit.circuit.library.standard_gates.u3.U3Gate,
    "CH": qiskit.circuit.library.standard_gates.h.CHGate,
    "CX": qiskit.circuit.library.standard_gates.x.CXGate,
    "Swap": qiskit.circuit.library.standard_gates.swap.SwapGate,
    "iSwap": qiskit.circuit.library.standard_gates.iswap.iSwapGate,
    "CSX": qiskit.circuit.library.standard_gates.sx.CSXGate,
    "DCX": qiskit.circuit.library.standard_gates.dcx.DCXGate,
    "CY": qiskit.circuit.library.standard_gates.y.CYGate,
    "CZ": qiskit.circuit.library.standard_gates.z.CZGate,
    "CPhase": qiskit.circuit.library.standard_gates.p.CPhaseGate,
    "CRX": qiskit.circuit.library.standard_gates.rx.CRXGate,
    "RXX": qiskit.circuit.library.standard_gates.rxx.RXXGate,
    "CRY": qiskit.circuit.library.standard_gates.ry.CRYGate,
    "RYY": qiskit.circuit.library.standard_gates.ryy.RYYGate,
    "CRZ": qiskit.circuit.library.standard_gates.rz.CRZGate,
    "RZX": qiskit.circuit.library.standard_gates.rzx.RZXGate,
    "RZZ": qiskit.circuit.library.standard_gates.rzz.RZZGate,
    "CU1": qiskit.circuit.library.standard_gates.u1.CU1Gate,
    "RCCX": qiskit.circuit.library.standard_gates.x.RCCXGate,
    "RC3X": qiskit.circuit.library.standard_gates.x.RC3XGate,
    "CCX": qiskit.circuit.library.standard_gates.x.CCXGate,
    "Unitary": qiskit.extensions.unitary.UnitaryGate,
    "MEASURE": qiskit.circuit.measure.Measure,
}

QiskitGate = Union[Measure, Gate, Instruction]


def get_qiskit_gate_data(gate: QiskitGate) -> dict:

    data = {"type": None, "matrix": None, "num_controls": 0}

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
            raise TranspilerError("Gate of type {} not supported".format(type(gate)))

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
        raise TranspilerError(f"Gate of type {gate_type} not supported for Qiskit transpile.")


def circuit_to_qiskit(cw, auto_measure=False) -> QuantumCircuit:

    qreg = QuantumRegister(cw.num_qubits)
    output_qubit_mapping = {index: Qubit(qreg, index) for index in range(len(qreg))}
    cw.output_qubit_mapping = output_qubit_mapping

    output_param_mapping = {
        pid: QiskitParameter(pid.name) for pid in cw.input_param_mapping.values()
    }

    # get instruction data to intermediate format
    # (will eventually include combing through moments)
    data = []
    measurement_qubit_indices = set()
    for instruction in cw.instructions:
        gate, qubits, measurement_qubits = instruction.transpile(
            "qiskit", output_qubit_mapping, output_param_mapping
        )
        data.append((gate, qubits, measurement_qubits))
        measurement_qubit_indices.update(measurement_qubits)

    # determine the length of the classical register and initialize
    if auto_measure:
        creg = ClassicalRegister(len(cw.num_qubits))
    elif len(measurement_qubit_indices) == 0:
        creg = None
    else:
        creg = ClassicalRegister(len(measurement_qubit_indices))
        # store how a qubit id maps to a clbit for the user
        clbit_mapping = {qubit: index for index, qubit in enumerate(measurement_qubit_indices)}

    if creg:
        output_circ = QuantumCircuit(qreg, creg, name="qBraid_transpiler_output")
    else:
        output_circ = QuantumCircuit(qreg, name="qBraid_transpiler_output")

    # add instructions to circuit
    for gate, qubits, measurement_qubits in data:
        clbits = None if not measurement_qubits else [clbit_mapping[q] for q in measurement_qubits]
        output_circ.append(gate, qubits, clbits)

    # auto measure
    if auto_measure:
        raise NotImplementedError

    return output_circ


def instruction_to_qiskit(
    iw, output_qubit_mapping, output_param_mapping
) -> Tuple[Instruction, list, list]:

    gate = iw.gate.transpile("qiskit", output_param_mapping)
    qubits = [output_qubit_mapping[q] for q in iw.qubits]

    if isinstance(gate, Measure):
        return gate, qubits, iw.qubits
    else:
        return gate, qubits, []


def gate_to_qiskit(gw, output_param_mapping):

    """Create qiskit gate from a qbraid gate wrapper object."""

    qiskit_params = gw.params.copy()

    for i, param in enumerate(qiskit_params):
        if isinstance(param, ParamID):
            qiskit_params[i] = output_param_mapping[param]

    data = {
        "type": gw.gate_type,
        "matrix": gw.matrix,
        "name": gw.name,
        "params": qiskit_params,
    }

    if gw.gate_type in qiskit_gates:
        return create_qiskit_gate(data)

    elif gw.base_gate:
        return gw.base_gate.transpile("qiskit").control(gw.num_controls)

    elif not (gw.matrix is None):
        data["name"] = data["type"]
        data["type"] = "Unitary"
        return create_qiskit_gate(data)

    else:
        raise TranspilerError(f"Gate type {gw.gate_type} not supported.")
