# Copyright (C) 2024 qBraid
#
# This file is part of the qBraid-SDK
#
# The qBraid-SDK is free software released under the GNU General Public License v3
# or later. You can redistribute and/or modify it under the terms of the GPL v3.
# See the LICENSE file in the project root or <https://www.gnu.org/licenses/gpl-3.0.html>.
#
# THERE IS NO WARRANTY for the qBraid-SDK, as per Section 15 of the GPL v3.

"""
Takes in OpenQASM 3 code and outputs an ASCII circuit representation

"""

import re

import numpy as np

controlled_gates = [
    "cx",
    "c3x",
    "c3sx",
    "c4x",
    "ccx",
    "ch",
    "crx",
    "cry",
    "crz",
    "cs",
    "csdg",
    "cswap",
    "csx",
    "cu",
    "cu1",
    "cu3",
    "cx",
    "cy",
    "cz",
    "ccz",
]

multi_qubit_gates = [
    "cp",
    "dcx",
    "ecr",
    "rccx",
    "rc3x",
    "rxx",
    "ryy",
    "rzz",
    "rzx",
    "xx_minus_yy",
    "xx_plus_yy",
    "iswap",
    "swap",
]

single_qubit_gates = [
    "h",
    "id",
    "p",
    "r",
    "rx",
    "ry",
    "rz",
    "s",
    "sdg",
    "sx",
    "sxdg",
    "t",
    "tdg",
    "U",
    "u1",
    "u2",
    "u3",
    "x",
    "y",
    "z",
]

q_c_reg_gates = ["m"]

all_gates = single_qubit_gates + multi_qubit_gates + controlled_gates + q_c_reg_gates


def is_valid_gate(line):
    """Checks if input string line is a valid OPENQASM gate"""
    if len(line) < 2:
        return False
    if len(line) > 2 and line[:2] == "//":
        return False
    if len(line) > 7 and line[:7] == "include":
        return False
    if len(line) > 8 and line[:8] == "OPENQASM":
        return False
    return True


def parse_gate_type(line, gates):
    """Returns gate type and params of a line"""
    params = None
    if "measure" in line:
        return ("m", params)

    gate_type = line.split(" ")[0]

    if "(" in line:
        gate_type = line.split("(")[0]
        params = re.search(r"\(.*\)", line)[0][1:-1]

    if gate_type not in gates:
        return (None, None)
    return (gate_type, params)


class Gate:
    """An individual gate in the circuit"""

    def __init__(self, line, num_qregs, num_cregs):
        """Initializes a gate"""

        assert is_valid_gate(line), "Invalid gate: " + str(line)

        self.gate_type, self.params = parse_gate_type(line, all_gates)

        assert self.gate_type is not None, "Gate is not found in list of possible gates"

        self.num_qregs = num_qregs
        self.num_cregs = num_cregs
        self.qregs = self.parse_qregs(line)
        self.cregs = self.parse_cregs(line)

    def parse_qregs(self, line):
        """Gets the quantum registers associated with the gate"""
        matches = re.findall(r"q\[.*?\]", line)
        qregs = []
        for match in matches:
            qregs.append(int(match[2:-1]))
        return qregs

    def parse_cregs(self, line):
        """Gets the classical registers associated with the gate"""
        matches = re.findall(r"b\[.*?\]", line)
        cregs = []
        for match in matches:
            cregs.append(int(match[2:-1]))
        return cregs

    def get_height(self):
        """Gets the height of the gate"""
        if self.gate_type in single_qubit_gates:
            return 1
        if self.gate_type in q_c_reg_gates:
            return self.num_qregs - min(self.qregs) + max(self.cregs) + 1
        return max(self.qregs) - min(self.qregs) + 1

    def get_width(self):
        """Gets the width of the gate"""
        gate_str = self.gate_type

        if self.params is not None:
            gate_str += "(" + self.params + ")"

        if gate_str in ("swap", "cswap"):
            return 3

        return len(gate_str) + 4

    def apply_gate_at_pos(self, gate_str, mat, pos):
        """Adds the gate at the given y coordinate in the matrix representation"""
        mat[pos, :] = ["|"] + ["-"] * (len(gate_str) + 2) + ["|"]
        mat[pos + 1, :] = ["|"] + [" "] + list(gate_str) + [" "] + ["|"]
        mat[pos + 2, :] = ["|"] + ["-"] * (len(gate_str) + 2) + ["|"]

        return mat

    def mat(self):
        """Outputs a matrix representation of the gate"""
        height = self.get_height()
        gate_str = self.gate_type
        mat = np.array([])

        if self.params is not None:
            gate_str += "(" + self.params + ")"

        if height == 1:
            mat = np.empty((3 * height, len(gate_str) + 4), dtype="str")
            mat = self.apply_gate_at_pos(gate_str, mat, 0)

        elif self.gate_type == "m":
            mat = np.empty((3 * height, len(gate_str) + 4), dtype="str")
            mat = self.apply_gate_at_pos(gate_str, mat, 0)

            c_reg_line = (
                [" "] * int((len(gate_str) + 4) / 2) + ["║"] + [" "] * int((len(gate_str) + 4) / 2)
            )
            mat[3 : 3 * height - 1, :] = [c_reg_line] * (3 * height - 4)
            mat[3 * height - 1, :] = [" "] * (len(gate_str) + 4)

        elif self.gate_type in controlled_gates:
            if gate_str == "cswap":
                mat = np.full((3 * height, 3), " ", dtype="str")
                mat[1:-1, 1] = ["|"] * (mat.shape[1] - 2)
                mat[(self.qregs[0] - min(self.qregs)) * 3 + 1, :2] = ["-", "■"]
                mat[(self.qregs[1] - min(self.qregs)) * 3 + 1, :2] = ["-", "X"]
                mat[(self.qregs[2] - min(self.qregs)) * 3 + 1, :2] = ["-", "X"]
                return mat

            mat = np.full((3 * height, len(gate_str) + 4), " ", dtype="str")
            mid = int(mat.shape[1] / 2)
            mat[1:-1, mid] = ["|"] * (mat.shape[0] - 2)

            for qreg in range(len(self.qregs) - 1):
                mat[(self.qregs[qreg] - min(self.qregs)) * 3 + 1, : mid + 1] = ["-"] * mid + ["■"]

            for qreg in range(height):
                if qreg != self.qregs[-1]:
                    mat[3 * qreg + 1, :mid] = ["-"] * mid
            mat = self.apply_gate_at_pos(gate_str, mat, (self.qregs[-1] - min(self.qregs)) * 3)

        elif self.gate_type in multi_qubit_gates:
            if gate_str == "swap":
                mat = np.empty((3 * height, 3), dtype="str")
                mat[0, :] = [" "] * 3
                mat[1, :] = ["-", "X", " "]
                mat[2 : 3 * height - 2, :] = [[" ", "|", " "]] * (3 * height - 4)
                mat[3 * height - 2, :] = ["-", "X", " "]
                mat[3 * height - 1, :] = [" "] * 3
                mat[range(1, 3 * height, 3), 0] = ["-"] * height

            else:
                mat = np.full((3 * height, len(gate_str) + 4), " ", dtype="str")
                mat[0, :] = ["|"] + ["-"] * (mat.shape[1] - 2) + ["|"]
                mat[1:-1, :] = ["|"] + [" "] * (mat.shape[1] - 2) + ["|"]
                for qreg_idx, _ in enumerate(self.qregs):
                    mat[(self.qregs[qreg_idx] - min(self.qregs)) * 3 + 1, 1] = qreg_idx
                mat[int(mat.shape[0] / 2), mat.shape[1] - len(gate_str) - 1 : -1] = list(gate_str)
                mat[-1, :] = ["|"] + ["-"] * (mat.shape[1] - 2) + ["|"]

        return mat


def get_collision(circuit, g):
    """Gets the collision position of a gate"""
    pos = circuit.shape[1] - 1
    collision = False
    reg_idxes = range(3 * min(g.qregs), 3 * (g.get_height() + min(g.qregs)))
    while not collision and pos > 0:
        for reg_idx in reg_idxes:
            if circuit[reg_idx][pos] != " ":
                collision = True
                break
        if collision:
            break
        pos -= 1

    if pos != 0:
        pos += 3

    return pos, reg_idxes


def add_gate(circuit, g, pos, reg_idxes):
    """Adds a gate to the circuit"""

    while pos + g.get_width() >= circuit.shape[1]:
        circuit = np.concatenate(
            [circuit, np.full((circuit.shape[0], circuit.shape[1]), " ", dtype=str)], axis=1
        )

    circuit[reg_idxes, pos : pos + g.get_width()] = g.mat()

    return circuit


def add_moment(circuit, moment):
    """Adds a moment to the circuit"""
    collisions = [get_collision(circuit, g)[0] for g in moment]
    pos = max(collisions)
    widths = [g.get_width() for g in moment]
    max_w = max(widths)

    for g in moment:
        _, reg_idxes = get_collision(circuit, g)
        centered_moment_pos = pos + int((max_w - g.get_width()) / 2)
        circuit = add_gate(circuit, g, centered_moment_pos, reg_idxes)
        circuit = add_wires(circuit, g, g.num_qregs, centered_moment_pos)

    return circuit


def get_circuit_height(qasm_str):
    """Gets the number of qubit and classical registers in the circuit"""
    num_qregs = 0
    num_cregs = 0
    for line in qasm_str.split("\n"):
        qreg_match = re.match(r"qreg (\w+)\[\d+\];", line)
        if qreg_match:
            num_qregs = int(re.search(r"\[(\d+)\]", line).group(1))
            continue
        creg_match = re.match(r"creg (\w+)\[\d+\];", line)
        if creg_match:
            num_cregs = int(re.search(r"\[(\d+)\]", line).group(1))
            continue
        if re.match(r"qubit\[.*\]", line):
            num_qregs = int(re.match(r"qubit\[.*\]", line)[0][6:-1])
            continue
        if re.match(r"bit\[.*\]", line):
            num_cregs = int(re.match(r"bit\[.*\]", line)[0][4:-1])
            continue

    return num_qregs, num_cregs


def get_collision_before_pos(circuit, x, y):
    """Gets the position of nearest collision with another gate"""
    while circuit[y, x] == " " and x >= 0:
        x -= 1
    return x


def add_wires(circuit, g, num_qregs, pos):
    """Adds wires to connect gates"""
    if pos == 0:
        return circuit

    start_wire = min(g.qregs)
    end_wire = max(g.qregs)
    if g.gate_type == "m":
        end_wire = num_qregs
    for y in range(3 * start_wire + 1, 3 * end_wire + 4, 3):
        while circuit[y, pos] == " ":
            pos += 1
        collision_pos = get_collision_before_pos(circuit, pos - 1, y)
        circuit[y, collision_pos + 1 : pos] = ["-"] * (pos - collision_pos - 1)

    return circuit


def add_cregs(circuit, num_cregs, end_pos):
    """Adds classical registers to the circuit"""
    for bit in range(num_cregs):
        y = -2 - (bit * 3)
        circuit[y, :end_pos] = ["="] * end_pos

    return circuit


def extend_qregs(circuit, num_qregs, end_pos):
    """Extends the quantum registers to the end of the circuit"""
    for qreg in range(num_qregs):
        eol_regex = re.search(r"(\S)\s*$", "".join(circuit[3 * qreg + 1]))
        eol_pos = eol_regex.regs[1][1]
        circuit[3 * qreg + 1, eol_pos:end_pos] = ["-"] * (end_pos - eol_pos)

    return circuit


def can_add_gate(m_qregs, m_cregs, gate):
    """Checks if a gate can be added to a moment"""
    if len(gate.qregs) != 0:
        min_qreg = min(gate.qregs)
        max_qreg = max(gate.qregs) if gate.gate_type not in q_c_reg_gates else gate.num_qregs
        for qreg in range(min_qreg, max_qreg + 1):
            if qreg in m_qregs:
                return False

    if len(gate.cregs) != 0:
        min_creg = min(gate.cregs) if gate.gate_type not in q_c_reg_gates else 0
        max_creg = max(gate.cregs)
        for creg in range(min_creg, max_creg + 1):
            if creg in m_cregs:
                return False

    return True


def get_moments(gates):
    """Splits up the circuit into moments"""
    moments = []
    while gates != []:
        gate = gates.pop(0)
        moment = [gate]
        m_qregs = list(gate.qregs)
        m_cregs = list(gate.cregs)
        gate_idx = 0
        while gate_idx < len(gates):
            gate = gates[gate_idx]
            if can_add_gate(m_qregs, m_cregs, gate):
                moment.append(gates.pop(gate_idx))
                gate_idx -= 1

            for qreg in gate.qregs:
                m_qregs.append(qreg)
            for creg in gate.cregs:
                m_cregs.append(creg)

            gate_idx += 1
        moments.append(moment)
    return moments


def _qasm3_drawer(qasm_str: str) -> str:
    """Iterates over the input string and returns the gates"""
    num_qregs, num_cregs = get_circuit_height(qasm_str)
    height = (num_qregs + num_cregs) * 3
    circuit = np.full((height, 50), " ", dtype=str)

    gates = []
    for line in qasm_str.split("\n"):
        valid = is_valid_gate(line)
        gate_type, _ = parse_gate_type(line, all_gates)
        if valid and gate_type is not None:
            g = Gate(line, num_qregs, num_cregs)
            gates.append(g)

    moments = get_moments(gates)
    for moment in moments:
        circuit = add_moment(circuit, moment)

    #    circuit, pos = add_gate(circuit, g)
    #    circuit = add_wires(circuit, g, num_qregs, pos)

    end_pos = circuit.shape[1]
    while np.all(circuit[:, end_pos - 1] == [" "] * circuit.shape[0]):
        end_pos -= 1
    end_pos += 1

    circuit = add_cregs(circuit, num_cregs, end_pos)
    circuit = extend_qregs(circuit, num_qregs, end_pos)

    padding = 5

    out = ""
    reg_idx = 0
    is_q_reg = True
    for row_idx, _ in enumerate(circuit):
        line = ""
        if row_idx % 3 == 1:
            if reg_idx < num_qregs and is_q_reg:
                line += ("q" + str(reg_idx)).ljust(padding, "-")
            elif is_q_reg:
                reg_idx = 0
                is_q_reg = False

            if not is_q_reg:
                line += ("c" + str(reg_idx)).ljust(padding, "=")
            reg_idx += 1
        else:
            line += " " * padding
        line += "".join(circuit[row_idx]).rstrip() + "\n"
        if line.strip() != "":
            out += line

    return out[:-1]


def qasm3_drawer(qasm_str: str) -> None:
    """Draws the circuit from the input string"""
    print(_qasm3_drawer(qasm_str))
