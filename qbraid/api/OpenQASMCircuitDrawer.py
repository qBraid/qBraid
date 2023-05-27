"""
Script to generate random OpenQASM 3.0 programs from restricted gate set

"""

import numpy as np

def random_circuit(num_qubits: int, num_instructions: int) -> Circuit:
    gate_set = [I(), X(), Y(), Z(), H(), S(), Si(), V(), Vi()]
    gate_set += [Rx(0.5), Ry(0.5), Rz(0.5), GPi(0.5), GPi2(0.5)]

    circ = Circuit()
    for _ in range(num_instructions):
        q = random.choice(range(num_qubits))
        gate = random.choice(gate_set)
        circ.add(Instruction(gate, [q]))
    return circ

two_qubit_gates = [
    "m"
]
one_qubit_gates = [
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

def parse_idx(expr):
    """
    Simple helper method to get the index contained between square brackets
    """
    return expr[expr.find("[")+1 : expr.find("]")]

def parse_open_qasm(fname):
    """
    Assumes first three lines contain:
        Line 1: the OPENQASM version number
        Line 2: the classical register
        Line 3: the qubit register
    This should be updated for robustness later
    
    Args:
        fname: File containing the OpenQASM 3.0 code to parse
    
    Returns:
        A tuple containing the classical and qubit registers
    """
    with open(fname) as f:
        line1, line2, line3 = f.readline(), f.readline(), f.readline()
        num_bits = int(parse_idx(line2)) # number of classical registers
        num_qubits = int(parse_idx(line3)) # number of qubit registers

        c_regs = ["c" + str(i) for i in range(num_bits)] # classical registers
        q_regs = [[]] * num_qubits # qubit registers

        for line in f: # Iterate over file
            line = line.strip().split() # Process the line into the correct format
            nargs = len(line) # Get the number of gate

            if nargs == 2: # Single qubit gate
                gate = line[0] # Get the gate
                
                params = ""
                if gate.find("(") != -1: # Check if gate has params
                    params = gate[gate.find("("):] # Store params
                    gate = gate[:gate.find("(")] # Get the gate without params

                qreg = int(parse_idx(line[1])) # The qubit register the gate acts on

                if gate in one_qubit_gates: # Ensure gate is valid
                    q_regs[qreg] = q_regs[qreg] + [gate + params] # Update qubit register

            elif nargs == 4: # Gate applied to multiple qubits
                if line[1] == "=": # Measurement operation
                    qreg = int(parse_idx(line[3])) # Index of qubit register to measure
                    creg = int(parse_idx(line[0])) # Index of classical bit to store measurement in
                    q_regs[qreg] = q_regs[qreg] + ['m' + str(creg)] # Add gate to correct register

    return c_regs, q_regs

def get_available_pos(gate, reg_idxes, mat, num_qubits, num_bits):
    """
    Gets the correct x and y coordinates to insert the gate
    x and y refer to the top left corner of the gate
    """
    
    if gate.find("(") != -1: # Parameterized gate
        gate = gate[:gate.find("(")] # Get just the name of the gate, not the parameters
        
    if gate not in one_qubit_gates: # Additional logic is necessary to write across multiple lines
        
        # Case for measurement gate
        if gate[0] == "m" and gate[1:].isdigit():
            

            reg_idxes = range(reg_idxes[0], (num_qubits+int(gate[1:]))) # Register indexes that need to be written over

    # Column counter to insert the gate, start at the far right and work backwards
    column_idx = len(mat[0])
    collision = False
    while column_idx != 0: # Can't go farther left
        for idx in range(len(reg_idxes)): # Check each register the gate will be overwriting
            if mat[reg_idxes[idx] * 3 + 1][column_idx-1] != ' ': # If not empty, then collision occurs
                collision = True
                column_idx += 3 # Move the gate three spaces to the right to avoid overwriting previous gates
                break
                
        if collision:
            break
        
        column_idx -= 1

    return column_idx, reg_idxes[0]*3

def display_circuit(fname):
    """
    Prints out the circuit gates after parsing
    """
    c_regs, q_regs = parse_open_qasm(fname)
    num_bits = len(c_regs)
    
    min_gate_width = 5
    
    total_gates_width = sum([sum([len(gate) + min_gate_width for gate in reg]) for reg in q_regs])*3
    mat = np.full((3*(len(q_regs) + num_bits), total_gates_width), ' ', dtype=str)
    
    num_gates = sum([len(reg) for reg in q_regs])
    longest_gate_sequence = max([len(reg) for reg in q_regs])
    
    for column in range(longest_gate_sequence):
        for reg_idx in range(len(q_regs)):
            if len(q_regs[reg_idx]) <= column:
                continue
            gate = q_regs[reg_idx][column]
            x, y = get_available_pos(gate, [reg_idx], mat, len(q_regs), num_bits)
            sep_dist = 3
            if x > 2:
                
                for idx in range(mat.shape[1]-1, 0, -1):
                    if mat[y+1, idx] == '|':
                        sep_dist = max(sep_dist, x - idx - 1)
                        break
                        
                mat[y+1, x-sep_dist:x] = ['-']*sep_dist
                
            mat[y:y+3,x] = ['|']*3
            mat[y, x+1:x+len(gate)+3] = ['-']*(len(gate)+2)
            mat[y+1, x+1:x+len(gate)+3] = [' '] + [c for c in gate] + [' ']
            mat[y+2, x+1:x+len(gate)+3] = ['-']*(len(gate)+2)
            mat[y:y+3,x+len(gate)+3] = ['|']*3
            
            if gate[0] in two_qubit_gates:
                mat[y+3:(len(q_regs)+int(gate[1:]))*3+1, x+int(len(gate)/2)+1] = ['‖'] * ((len(q_regs)+int(gate[1:]))*3+1-y-3)
    
    for bit in range(num_bits):
        mat[-2-(bit*3), :] = ['='] * mat.shape[1]
    
    total_circuit_len = 0
    for reg in mat:
        for char_idx in range(len(reg)):
            if reg[char_idx] != ' ' and reg[char_idx] != '=':
                total_circuit_len = max(total_circuit_len, char_idx)
    
    mat[:, total_circuit_len + 1:] = ''
    
    padding = 5
    
    str_out = ""
    reg_idx = 0
    is_q_reg = True
    for row_idx in range(len(mat)):
        if row_idx % 3 == 1:
            if reg_idx < len(q_regs) and is_q_reg:
                str_out += ("q" + str(reg_idx)).ljust(padding, ' ')
            elif is_q_reg:
                reg_idx = 0
                is_q_reg = False
                str_out += "".join(c_regs[reg_idx]).ljust(padding, ' ')
            else:
                str_out += "".join(c_regs[reg_idx]).ljust(padding, ' ')
            reg_idx += 1
        else:
            str_out += ' ' * padding
        # str_out += "".join(header[row_idx])
        str_out += ''.join(mat[row_idx]) + "\n"
    
    return str_out
