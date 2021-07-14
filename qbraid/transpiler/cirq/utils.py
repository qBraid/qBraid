from cirq import Gate
from cirq.ops.common_gates import *
from cirq.ops.controlled_gate import ControlledGate
from cirq.ops.gate_features import SingleQubitGate
from cirq.ops.matrix_gates import MatrixGate
from cirq.ops.swap_gates import *
from cirq.ops.three_qubit_gates import *
import numpy as np


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
        data["matrix"] = cirq.unitary(gate)

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

    else:
        if data["type"] != "MEASURE":
            raise TypeError("Gate of type {} not supported".format(type(gate)))

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

    elif gate_type == "S":
        return cirq_gates["S"](exponent=0.5)
    elif gate_type == "T":
        return cirq_gates["T"](exponent=0.25)

    # single-qubit, one-parameter gates
    elif gate_type in ("RX", "RY", "RZ"):
        theta = data["params"][0]
        # theta = data["params"][0] / np.pi
        return cirq_gates[gate_type](theta)

    elif gate_type == "Phase":
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

    elif gate_type == "Unitary":
        n_qubits = int(np.log2(len(matrix)))
        unitary = cirq_gates[gate_type](matrix)
        give_cirq_gate_name(unitary, "U", n_qubits)
        return unitary

    # error
    else:
        raise TypeError(f"Gate of type {gate_type} not supported for Cirq transpile.")
