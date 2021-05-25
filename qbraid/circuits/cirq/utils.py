from cirq import Gate
from cirq.ops.common_gates import *
from cirq.ops.swap_gates import *
from cirq.ops.three_qubit_gates import *
from cirq.ops.gate_features import SingleQubitGate, TwoQubitGate, ThreeQubitGate
import numpy as np
from ..exceptions import CircuitError


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
    def _circuit_diagram_info_():
        return "U3"


class CirqUnitaryGate(Gate):
    def __init__(self, matrix: np.ndarray, name: str = "U"):
        self._name = name
        self._matrix = matrix
        super(CirqUnitaryGate, self)

    def _num_qubits_(self):
        return int(np.log2(len(self._matrix)))

    def _unitary_(self):
        return self._matrix

    def _circuit_diagram_info_(self):
        n = self._num_qubits_()
        symbols = [self._name for _ in range(n)]
        return symbols


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
    "Swap": SWAP,
    "iSwap": ISWAP,
    "CZ": CZPowGate,
    "CPhase": cphase,
    "CCZ": CCZPowGate,
    "CCX": CCXPowGate,
    "MEASURE": MeasurementGate,
    "U3": CirqU3Gate,
    "Unitary": CirqUnitaryGate,
}

CirqGate = Union[SingleQubitGate, TwoQubitGate, ThreeQubitGate, MeasurementGate]


def get_cirq_gate_data(gate: CirqGate) -> dict:
    """

    :param gate:
    :return:
    """
    data = {
        "type": None,
        "params": [],
        "matrix": None,
        "num_controls": 0
    }

    try:
        data["matrix"] = cirq.unitary(gate)
    except AttributeError:
        pass

    # measurement gate
    if isinstance(gate, MeasurementGate):
        data["type"] = "MEASURE"

    # single qubit gates
    elif isinstance(gate, HPowGate):
        if gate.exponent == 1:
            data["type"] = "H"
        else:
            data["type"] = "HPow"

            t = gate.exponent
            data["params"] = [t]

    elif isinstance(gate, XPowGate):
        if gate.exponent == 1:
            data["type"] = "X"
        elif gate.global_shift == -0.5:
            params = [gate.exponent * np.pi]
            data["type"] = "RX"
            data["params"] = params
        else:
            data["type"] = "XPow"

            t = gate.exponent
            data["params"] = [t]

    elif isinstance(gate, YPowGate):
        if gate.exponent == 1:
            data["type"] = "Y"
        else:
            data["type"] = "YPow"

            t = gate.exponent
            data["params"] = [t]

    elif isinstance(gate, ZPowGate):
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
            pass
    elif isinstance(gate, CSwapGate):
        data["type"] = "CSwap"

    elif isinstance(gate, ControlledGate):
        data["type"] = "Controlled"
        data["base_gate_data"] = get_cirq_gate_data(gate.sub_gate)
        data["num_controls"] = gate.num_controls()

    else:
        raise CircuitError("Gate of type {} not supported".format(type(gate)))

    return data


def create_cirq_gate(data):
    gate_type = data["type"]
    params = data["params"]

    # single-qubit, no parameters
    if gate_type in ("H", "X", "Y", "Z"):
        return cirq_gates[gate_type]()

    elif gate_type == "S":
        return cirq_gates["S"](exponent=0.5)
    elif gate_type == "T":
        return cirq_gates["T"](exponent=0.25)

    # single-qubit, one-parameter gates
    elif gate_type in ("RX", "RY", "RZ"):
        theta = data["params"][0] / np.pi
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
        return cirq_gates[gate_type]()

    # multi-qubit
    elif gate_type in "CCX":
        return cirq_gates[gate_type]()

    # measure
    elif gate_type == "MEASURE":
        return cirq_gates[gate_type]()

    # custom gates
    elif gate_type == "U3":
        return CirqU3Gate(*params)

    elif gate_type == "Unitary":
        if data["name"] == "Unitary":
            data["name"] = "U"
        return cirq_gates["Unitary"](data["matrix"], name=data["name"])

    # error
    else:
        raise CircuitError("{} gate not supported for Cirq conversion.".format(gate_type))
