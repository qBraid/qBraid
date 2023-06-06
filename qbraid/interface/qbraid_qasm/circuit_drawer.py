import numpy as np
import re

one_reg_gates= [
    "i",
    "x",
    "y",
    "z",
    "h",
    "s",
    "si",
    "v",
    "vi",
    "rx",
    "ry",
    "rz",
    "gpi",
    "gpi2"
]

two_reg_gates = [
    "cx"
]

q_c_reg_gates = [
    "m"
]

all_gates = one_reg_gates + two_reg_gates + q_c_reg_gates

def is_valid_gate(line):
    """
    Checks if input string line is a valid OPENQASM gate
    """
    if len(line) < 2:
        return False 
    elif len(line) > 2 and line[:2] == "//":
        return False 
    elif len(line) > 7 and line[:7] == "include":
        return False 
    elif len(line) > 8 and line[:8] == "OPENQASM":
        return False 
    return True

def parse_gate_type(line, all_gates):
    params = None
    if "measure" in line:
        return ("m", params)

    gate_type = line.split(" ")[0]
    if "(" in gate_type:
        params = re.search(r"\(.*\)", gate_type)
        if params is not None:
            params = params[0][1:-1]
        gate_type = gate_type[:gate_type.find("(")]

    if gate_type not in all_gates: 
        return (None, None)
    return (gate_type, params) 

class Gate:
    def __init__(self, line, num_qregs, num_cregs):
        """
        param line: input string containing information about the gate
        """

        assert is_valid_gate(line), "Invalid gate: " + str(line)

        self.gate_type, self.params = parse_gate_type(line, all_gates)

        assert self.gate_type is not None, "Gate is not found in list of possible gates"

        self.num_qregs = num_qregs
        self.num_cregs = num_cregs
        self.qregs = self.parse_qregs(line)
        self.cregs = self.parse_cregs(line)

    def parse_qregs(self, line):
        matches = re.findall(r"q\[.*?\]", line)
        qregs = []
        for match in matches:
            qregs.append(int(match[2:-1]))
        return qregs 

    def parse_cregs(self, line):
        matches = re.findall(r"b\[.*?\]", line)
        cregs = []
        for match in matches:
            cregs.append(int(match[2:-1]))
        return cregs 

    def get_height(self):
        if self.gate_type in one_reg_gates:
            return 1
        elif self.gate_type in two_reg_gates:
            return max(self.qregs) - min(self.qregs) + 1
        elif self.gate_type in q_c_reg_gates:
            return self.num_qregs - min(self.qregs) + max(self.cregs) + 1
        return -1
    
    def apply_gate_at_pos(self, gate_str, mat, pos):
        
        mat[pos, :] = ["|"] + ["-"] * (len(gate_str) + 2) + ["|"]
        mat[pos + 1, :] = ["|"] + [" "] + [c for c in gate_str] + [" "] + ["|"]
        mat[pos + 2, :] = ["|"] + ["-"] * (len(gate_str) + 2) + ["|"]

        return mat

    def get_width(self):
        gate_str = self.gate_type

        if self.params is not None:
            gate_str += "(" + self.params + ")"

        return len(gate_str) + 4

    def mat(self):
        height = self.get_height()
        gate_str = self.gate_type
        mat = np.array([])

        if self.params is not None:
            gate_str += "(" + self.params + ")"

        if height == 1:
            mat = np.empty((3 * height, len(gate_str) + 4), dtype="str")
            mat = self.apply_gate_at_pos(gate_str, mat, 0)

        elif gate_str == "m":
            mat = np.empty((3 * height, len(gate_str) + 4), dtype="str")
            mat = self.apply_gate_at_pos(gate_str, mat, 0)
            
            c_reg_line = [" "] * int((len(gate_str) + 4)/2) + ["║"] + [" "] * int((len(gate_str) + 4)/2)
            mat[3:3*height - 1, :] = [c_reg_line] * (3 * height - 4) 
            mat[3*height - 1, :] = [" "] * (len(gate_str) + 4)

        elif gate_str == "cx":
            mat = np.empty((3 * height, len(gate_str) + 4), dtype="str")
            parity_check = 1 - (len(gate_str) % 2)
            q_reg_line = [" "] * int((len(gate_str) + 4)/2 - parity_check) + ["|"] + [" "] * int((len(gate_str) + 4)/2)
            mat[1:, :] = [q_reg_line] * ((3 * height) - 1) 

            if self.qregs[0] < self.qregs[1]:
                mat[0, :] = [" "] * ((len(gate_str) + 4))
                mat[1, :] = ["-"] * int((len(gate_str) + 4)/2 - parity_check) + ["■"] + [" "] * int((len(gate_str) + 4)/2)
                mat = self.apply_gate_at_pos(gate_str, mat, (3 * height) - 3)
            else:
                mat[(3 * height) - 1, :] = [" "] * ((len(gate_str) + 4))
                mat[(3 * height) - 2, :] = ["-"] * int((len(gate_str) + 4)/2 - parity_check) + ["■"] + [" "] * int((len(gate_str) + 4)/2)
                mat = self.apply_gate_at_pos(gate_str, mat, 0)
            
        return mat 

def add_gate(circuit, g):
    pos = circuit.shape[1] - 1
    collision = False
    reg_idxes = range(3*min(g.qregs), 3*(g.get_height()+min(g.qregs)))
    while not collision and pos > 0:
        for reg_idx in reg_idxes:
            if circuit[reg_idx][pos] != " ":
                collision = True
                break
        pos -= 1

    if pos != 0:
        pos += 3

    while pos + g.get_width() >= circuit.shape[1]:
        # Expand circuit
        circuit = np.concatenate([circuit, np.full((circuit.shape[0], circuit.shape[1]), " ", dtype=str)], axis=1)

    circuit[reg_idxes, pos:pos+g.get_width()] = g.mat() 

    return circuit, pos
        

def get_circuit_height(qasm_str):

    num_qregs = 0
    num_cregs = 0
    for line in qasm_str.split("\n"):
        if re.match(r"qreg q\[.*\]", line):
            num_qregs = int(re.match(r"qreg q\[.*\]", line)[0][7:-1])
            continue
        elif re.match(r"creg q\[.*\]", line):
            num_cregs = int(re.match(r"creg q\[.*\]", line)[0][7:-1])
            continue
        elif re.match(r"qubit\[.*\]", line):
            num_qregs = int(re.match(r"qubit\[.*\]", line)[0][6:-1])
            continue
        elif re.match(r"bit\[.*\]", line):
            num_cregs = int(re.match(r"bit\[.*\]", line)[0][4:-1])
            continue

    return num_qregs, num_cregs

def get_collision_before_pos(circuit, x, y):
    while circuit[y, x] == ' ' and x > 0:
        x -= 1
    return x

def add_wires(circuit, g, pos):
    if pos == 0:
        return circuit
    height = g.get_height()
    for qreg in g.qregs:
        y = qreg * 3 + 1
        collision_pos = get_collision_before_pos(circuit, pos - 1, y)
        circuit[y, collision_pos + 1:pos] = ["-"] * (pos - collision_pos - 1)

    return circuit

def add_cregs(circuit, num_cregs):

    for bit in range(num_cregs):
        x = circuit.shape[1]
        y = -2 - (bit * 3) 
        while circuit[y][x - 1] == ' ' and x > 0:
            x -= 1
        x += 1
        circuit[y, :x] = ['='] * x

    return circuit

def draw_circuit(qasm_str):
    num_qregs, num_cregs = get_circuit_height(qasm_str)
    height = (num_qregs + num_cregs) * 3
    circuit = np.full((height, 50), " ", dtype=str)

    for line in qasm_str.split("\n"):

        valid = is_valid_gate(line)
        gate_type, _ = parse_gate_type(line, one_reg_gates + two_reg_gates + q_c_reg_gates)
        if valid and gate_type is not None: 
            g = Gate(line, num_qregs, num_cregs)
            circuit, pos = add_gate(circuit, g)
            circuit = add_wires(circuit, g, pos)

    circuit = add_cregs(circuit, num_cregs)

    padding = 5
    
    str_out = ""
    reg_idx = 0
    is_q_reg = True
    for row_idx in range(len(circuit)):
        if row_idx % 3 == 1:
            if reg_idx < num_qregs and is_q_reg:
                str_out += ("q" + str(reg_idx)).ljust(padding, '-')
            elif is_q_reg:
                reg_idx = 0
                is_q_reg = False

            if not is_q_reg:
                str_out += ("c" + str(reg_idx)).ljust(padding, '=')
            reg_idx += 1
        else:
            str_out += ' ' * padding
        str_out += ''.join(circuit[row_idx]) + "\n"
    
    return str_out

circ_str = """
OPENQASM 3.0;
bit[2] b;
qubit[3] q;
cx q[2], q[1];
gpi2(0.5) q[2];
h q[1];
y q[2];
cx q[1], q[2];
rx(0.5) q[1];
b[0] = measure q[2];
b[1] = measure q[1];"""

print(draw_circuit(circ_str))
