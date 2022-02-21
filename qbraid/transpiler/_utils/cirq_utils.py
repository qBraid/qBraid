from typing import Union

import numpy as np
from cirq import Circuit, Gate, GridQubit, LineQubit, NamedQubit, Qid, unitary
from cirq.ops import CSwapGate, MeasurementGate
from cirq.ops.common_gates import (
    CXPowGate,
    CZPowGate,
    HPowGate,
    XPowGate,
    YPowGate,
    ZPowGate,
    cphase,
    rx,
    ry,
    rz,
)
from cirq.ops.controlled_gate import ControlledGate
from cirq.ops.gate_features import SingleQubitGate
from cirq.ops.identity import IdentityGate
from cirq.ops.matrix_gates import MatrixGate
from cirq.ops.measure_util import measure as CirqMeasure
from cirq.ops.moment import Moment
from cirq.ops.swap_gates import ISwapPowGate, SwapPowGate
from cirq.ops.three_qubit_gates import CCXPowGate, CCZPowGate
from sympy import Symbol

from qbraid.transpiler.parameter import ParamID

from ..exceptions import TranspilerError


class CirqU3Gate(SingleQubitGate):
    def __init__(self, theta, phi, lam):
        self._theta = theta
        self._phi = phi
        self._lam = lam

        super(CirqU3Gate, self)

    def _unitary_(self):
        c = np.cos(self._theta / 2)
        s = np.sin(self._theta / 2)
        phi = self._phi
        lam = self._lam

        return np.array(
            [
                [c, -np.exp(complex(0, lam)) * s],
                [np.exp(complex(0, phi)) * s, np.exp(complex(0, phi + lam)) * c],
            ]
        )

    @staticmethod
    def _circuit_diagram_info_(args):
        return "U3"


cirq_gates = {
    "H": HPowGate,
    "X": XPowGate,
    "Y": YPowGate,
    "Z": ZPowGate,
    "S": ZPowGate,
    "T": ZPowGate,
    "I": IdentityGate,
    "HPow": HPowGate,
    "XPow": XPowGate,
    "YPow": YPowGate,
    "ZPow": ZPowGate,
    "RX": rx,
    "RY": ry,
    "RZ": rz,
    "Phase": ZPowGate,
    "U1": ZPowGate,
    "CX": CXPowGate,
    "Swap": SwapPowGate,
    "iSwap": ISwapPowGate,
    "CZ": CZPowGate,
    "CPhase": cphase,
    "CCZ": CCZPowGate,
    "CCX": CCXPowGate,
    "MEASURE": MeasurementGate,
    "U3": CirqU3Gate,
    "Unitary": MatrixGate,
}

CirqGate = Union[Gate, MeasurementGate]


def get_cirq_gate_data(gate: CirqGate) -> dict:
    """Returns cirq gate data."""

    data = {"type": None, "params": [], "matrix": None, "num_controls": 0}

    # measurement gate
    if isinstance(gate, MeasurementGate):
        data["type"] = "MEASURE"
    else:
        data["matrix"] = unitary(gate)

    # single qubit gates
    if isinstance(gate, HPowGate):
        if gate.exponent == 1:
            data["type"] = "H"
        else:
            data["type"] = "HPow"

            t = gate.exponent
            data["params"] = [t]

    elif isinstance(gate, XPowGate):
        if gate.global_shift == -0.5:
            data["type"] = "RX"
            data["params"] = [gate.exponent * np.pi]
        elif gate.global_shift == 0.0 and gate.exponent == 1:
            data["type"] = "X"
        else:
            data["type"] = "XPow"
            data["params"] = [gate.exponent]

    elif isinstance(gate, YPowGate):
        if gate.global_shift == -0.5:
            data["type"] = "RY"
            data["params"] = [gate.exponent * np.pi]
        elif gate.global_shift == 0 and gate.exponent == 1:
            data["type"] = "Y"
        else:
            data["type"] = "YPow"
            data["params"] = [gate.exponent]

    elif isinstance(gate, ZPowGate):
        if gate.global_shift == 0:
            if gate.exponent == 1:
                data["type"] = "Z"
            elif gate.exponent == 0.5:
                data["type"] = "S"
            elif gate.exponent == 0.25:
                data["type"] = "T"
            else:
                data["type"] = "Phase"
                t = gate.exponent
                lam = t * np.pi
                data["params"] = [lam]
        elif gate.global_shift == -0.5:
            data["type"] = "RZ"
            params = [gate.exponent * np.pi]
            data["params"] = params
        else:
            data["type"] = "ZPow"
            data["params"] = [gate.exponent]

    elif isinstance(gate, IdentityGate):
        data["type"] = "I"

    # two qubit gates
    elif isinstance(gate, CXPowGate):
        if gate.exponent == 1:
            data["type"] = "CX"
        else:
            data["type"] = "CXPow"
    elif isinstance(gate, CZPowGate):
        if gate.exponent == 1:
            data["type"] = "CZ"
        else:
            data["type"] = "CZPow"
    # three qubit gates
    elif isinstance(gate, CCZPowGate):
        if gate.exponent == 1:
            data["type"] = "CCZ"
        else:
            data["type"] = "CCZPow"
    elif isinstance(gate, CCXPowGate):
        if gate.exponent == 1:
            data["type"] = "CCX"
        else:
            raise NotImplementedError
    elif isinstance(gate, SwapPowGate):
        if gate.exponent == 1:
            data["type"] = "Swap"
        else:
            raise NotImplementedError
    elif isinstance(gate, ISwapPowGate):
        if gate.exponent == 1:
            data["type"] = "iSwap"
        else:
            raise NotImplementedError
    elif isinstance(gate, CSwapGate):
        data["type"] = "CSwap"

    elif isinstance(gate, ControlledGate):
        data["type"] = "Controlled"
        data["base_gate_data"] = get_cirq_gate_data(gate.sub_gate)
        data["num_controls"] = gate.num_controls()

    elif isinstance(gate, CirqU3Gate) or data["matrix"] is not None:
        data["type"] = "Unitary"

    else:
        if data["type"] != "MEASURE":
            raise TranspilerError("Gate of type {} not supported".format(type(gate)))

    return data


def give_cirq_gate_name(cirq_gate, name, n_qubits):
    def _circuit_diagram_info_(args):
        return name, *(name,) * (n_qubits - 1)

    cirq_gate._circuit_diagram_info_ = _circuit_diagram_info_


def create_cirq_gate(data):
    gate_type = data["type"]
    params = data["params"]
    matrix = data["matrix"]

    # single-qubit, no parameters
    if gate_type in ("H", "X", "Y", "Z"):
        return cirq_gates[gate_type]()

    elif gate_type == "I":
        return cirq_gates["I"](num_qubits=1)

    elif gate_type == "S":
        return cirq_gates["S"](exponent=0.5)
    elif gate_type == "T":
        return cirq_gates["T"](exponent=0.25)

    # single-qubit, one-parameter gates
    elif gate_type in ("RX", "RY", "RZ"):
        theta = data["params"][0]
        # theta = data["params"][0] / np.pi
        return cirq_gates[gate_type](theta)

    elif gate_type in ("HPow", "XPow", "YPow", "ZPow"):
        exponent = data["params"][0]
        return cirq_gates[gate_type](exponent=exponent)

    elif gate_type in ("Phase", "U1"):
        t = data["params"][0] / np.pi
        return cirq_gates["Phase"](exponent=t)

    # two-qubit, no parameters
    elif gate_type in ("CX", "CZ"):
        return cirq_gates[gate_type]()  # default exponent = 1

    elif gate_type in "CPhase":
        return cirq_gates[gate_type](data["params"][0])

    elif gate_type in ("Swap", "iSwap"):
        return cirq_gates[gate_type](exponent=1.0)

    # multi-qubit
    elif gate_type in "CCX":
        return cirq_gates[gate_type]()

    # measure
    elif gate_type == "MEASURE":
        return "CirqMeasure"  # cirq_gates[gate_type](data["params"][0])

    # custom gates
    elif gate_type == "U3":
        return CirqU3Gate(*params)

    elif gate_type == "Unitary" or matrix is not None:
        n_qubits = int(np.log2(len(matrix)))
        unitary_gate = cirq_gates[gate_type](matrix)
        give_cirq_gate_name(unitary_gate, "U", n_qubits)
        return unitary_gate

    # error
    else:
        raise TranspilerError(f"Gate of type {gate_type} not supported for Cirq transpile.")


def circuit_to_cirq(cw, auto_measure=False, output_qubit_mapping=None, output_param_mapping=None):
    output_circ = Circuit()

    if not output_qubit_mapping:
        qubits = list(reversed([LineQubit(x) for x in range(len(cw.qubits))]))
        output_qubit_mapping = {x: qubits[x] for x in range(len(qubits))}

    if not output_param_mapping:
        output_param_mapping = {pid: Symbol(pid.name) for pid in cw.params}
        # print(output_param_mapping)
        # print(cw.params)

    if cw.moments:
        for m in cw.moments:
            output_circ.append(
                m.transpile(
                    "cirq",
                    output_qubit_mapping,
                    output_param_mapping,
                )
            )
    else:
        for instruction in cw.instructions:
            output_circ.append(
                instruction.transpile(
                    "cirq",
                    output_qubit_mapping,
                    output_param_mapping,
                )
            )

    # auto measure
    if auto_measure:
        raise NotImplementedError

    return output_circ


def moment_to_cirq(mw, output_qubit_mapping, output_param_mapping):
    return Moment(
        [i.transpile("cirq", output_qubit_mapping, output_param_mapping) for i in mw.instructions]
    )


def instruction_to_cirq(iw, output_qubit_mapping, output_param_mapping):

    gate = iw.gate.transpile("cirq", output_param_mapping)
    mapping = [output_qubit_mapping[x] for x in iw.qubits]

    if gate == "CirqMeasure":
        return [CirqMeasure(q, key=str(q.x)) for q in mapping]
    elif isinstance(gate, MatrixGate):
        qubits = list(reversed(mapping))
    else:
        qubits = mapping
    return gate(*qubits)


def gate_to_cirq(gw, output_param_mapping):
    """Create cirq gate from a qbraid gate wrapper object."""

    cirq_params = [output_param_mapping[p] if isinstance(p, ParamID) else p for p in gw.params]

    data = {
        "type": gw.gate_type,
        "matrix": gw.matrix,
        "name": gw.name,
        "params": cirq_params,
    }

    if gw.gate_type in cirq_gates:
        return create_cirq_gate(data)

    elif gw.base_gate:
        return gw.base_gate.transpile("cirq", output_param_mapping).controlled(gw.num_controls)

    elif not (gw.matrix is None):
        data["name"] = data["type"]
        data["type"] = "Unitary"
        return create_cirq_gate(data)

    else:
        raise TranspilerError(f"Gate type {gw.gate_type} not supported.")


def int_from_qubit(qubit: Qid) -> int:
    if isinstance(qubit, LineQubit):
        index = int(qubit)
    elif isinstance(qubit, GridQubit):
        index = qubit.row
    elif isinstance(qubit, NamedQubit):
        # Only correct if numbered sequentially
        index = int(qubit._comparison_key().split(":")[0][7:])
    else:
        raise ValueError(
            "Expected qubit of type 'GridQubit' 'LineQubit' or 'NamedQubit'"
            f"but instead got {type(qubit)}"
        )
    return index
