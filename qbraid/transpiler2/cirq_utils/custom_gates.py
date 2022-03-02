import fractions
from typing import Optional, Tuple

import numpy as np
import cirq
from cirq import (
    Circuit,
    Gate,
    MatrixGate,
    Operation,
    value,
    OP_TREE,
    IdentityGate,
    TwoQubitDiagonalGate,
    CircuitDiagramInfo,
)

class U2Gate(Gate):
    def __init__(self, phi, lam):
        self._phi = float(phi)
        self._lam = float(lam)

        super(U2Gate, self)

    def _num_qubits_(self) -> int:
        return 1

    def _unitary_(self):
        isqrt2 = 1 / np.sqrt(2)
        phi = self._phi
        lam = self._lam

        return np.array(
            [
                [isqrt2, -np.exp(1j * lam) * isqrt2],
                [
                    np.exp(1j * phi) * isqrt2,
                    np.exp(1j * (phi + lam)) * isqrt2,
                ],
            ],
        )

    def _circuit_diagram_info_(self, args):
        cirq_phi = self._phi / np.pi
        cirq_lam = self._lam / np.pi
        return f"U2({cirq_phi}, {cirq_lam})"

    def __str__(self) -> str:
        cirq_phi = fractions.Fraction(self._phi / np.pi)
        cirq_lam = fractions.Fraction(self._lam / np.pi)
        gate_str = f"U2({cirq_phi},{cirq_lam})"
        frac_str = gate_str.replace("/", "π/")
        return frac_str.replace("1π", "π")


class U3Gate(Gate):
    def __init__(self, theta, phi, lam):
        self._theta = float(theta)
        self._phi = float(phi)
        self._lam = float(lam)

        super(U3Gate, self)

    def _num_qubits_(self) -> int:
        return 1

    def _unitary_(self):
        cos = np.cos(self._theta / 2)
        sin = np.sin(self._theta / 2)
        phi = self._phi
        lam = self._lam

        return np.array(
            [
                [cos, -np.exp(complex(0, lam)) * sin],
                [
                    np.exp(complex(0, phi)) * sin,
                    np.exp(complex(0, phi + lam)) * cos,
                ],
            ]
        )

    def _circuit_diagram_info_(self, args):
        cirq_theta = self._theta / np.pi
        cirq_phi = self._phi / np.pi
        cirq_lam = self._lam / np.pi
        return f"U3({cirq_theta}, {cirq_phi}, {cirq_lam})"

    def __str__(self) -> str:
        cirq_theta = fractions.Fraction(self._theta / np.pi)
        cirq_phi = fractions.Fraction(self._phi / np.pi)
        cirq_lam = fractions.Fraction(self._lam / np.pi)
        gate_str = f"U3({cirq_theta},{cirq_phi},{cirq_lam})"
        frac_str = gate_str.replace("/", "π/")
        return frac_str.replace("1π", "π")


class RZZGate(Gate):
    def __init__(self, theta):
        self._theta = float(theta)

        super(RZZGate, self)

    def _num_qubits_(self) -> int:
        return 2

    def _unitary_(self):
        itheta2 = 1j * float(self._theta) / 2
        return np.array(
            [
                [np.exp(-itheta2), 0, 0, 0],
                [0, np.exp(itheta2), 0, 0],
                [0, 0, np.exp(itheta2), 0],
                [0, 0, 0, np.exp(-itheta2)],
            ],
        )

    def _circuit_diagram_info_(self, args):
        theta_radians = self._theta / np.pi
        rounded_theta = np.array(theta_radians)
        if args.precision is not None:
            rounded_theta = rounded_theta.round(args.precision)
        gate_str = f"RZZ({rounded_theta})"
        return CircuitDiagramInfo((gate_str, gate_str))


@value.value_equality
class ZPowGate(cirq.ZPowGate):
    def _qasm_(self, args: "cirq.QasmArgs", qubits: Tuple["cirq.Qid", ...]) -> Optional[str]:
        args.validate_version("2.0")
        if self._global_shift == 0:
            if self._exponent == 0.25:
                return args.format("t {0};\n", qubits[0])
            if self._exponent == -0.25:
                return args.format("tdg {0};\n", qubits[0])
            if self._exponent == 0.5:
                return args.format("s {0};\n", qubits[0])
            if self._exponent == -0.5:
                return args.format("sdg {0};\n", qubits[0])
            if self._exponent == 1:
                return args.format("z {0};\n", qubits[0])
            return args.format("p({0:half_turns}) {1};\n", self._exponent, qubits[0])
        return args.format("rz({0:half_turns}) {1};\n", self._exponent, qubits[0])


def _give_cirq_gate_name(gate: Gate, name: str, n_qubits: int) -> Gate:
    def _circuit_diagram_info_(args):
        return name, *(name,) * (n_qubits - 1)

    gate._circuit_diagram_info_ = _circuit_diagram_info_

def matrix_gate(matrix: np.ndarray) -> MatrixGate:
    n_qubits = int(np.log2(len(matrix)))
    unitary_gate = MatrixGate(matrix)
    _give_cirq_gate_name(unitary_gate, "U", n_qubits)
    return unitary_gate

def rzz(theta):
    if theta == 0:
        return IdentityGate(2)
    elif theta == 2 * np.pi:
        return TwoQubitDiagonalGate([np.pi] * 4)
    else:
        return RZZGate(theta)

def _map_zpow(op: Operation, _: int) -> OP_TREE:
    if isinstance(op.gate, cirq.ZPowGate):
        yield ZPowGate(exponent=op.gate.exponent, global_shift=op.gate.global_shift)(op.qubits[0])
    else:
        yield op

def _map_zpow_and_unroll(circuit: Circuit) -> Circuit:
    return cirq.map_operations_and_unroll(circuit, _map_zpow)