import sys

qasm_file = sys.argv[1]

python_code = [
    "import numpy as np\n" "from braket.circuits import Circuit\n\n",
    "circuit = Circuit()\n",
]

num_qubits = 0


def qasm_line_to_braket(op, args):
    if op in ["h", "x", "y", "z", "s", "t", "sx", "sxdg", "sdg", "tdg"]:
        q = args[0][2]
        if op in ["sx", "sxdg", "sdg", "tdg"]:
            op = op.replace("sx", "v")
            op = op.replace("dg", "i")
        return f"circuit.{op}({q})\n"
    if op in ["cx", "swap"]:
        qs = args[0].split(",")
        q0 = qs[0][2]
        q1 = qs[1][2]
        if op == "cx":
            op = "cnot"
        return f"circuit.{op}({q0}, {q1})\n"
    return ""


# read in qasm file
qasm_in = open(qasm_file, "r")
qasm_code = qasm_in.readlines()

for line in qasm_code:
    expr = line.strip().split(" ")
    op = expr[0]
    args = expr[1:]
    if op == "qreg":
        num_qubits = int(expr[1][2])
    else:
        py_line = qasm_line_to_braket(op, args)
        if py_line != "":
            python_code.append(py_line)

print_circuit = f"\nprint(circuit)\n"
python_code.append(print_circuit)

#  writing to file
braket_out = open("braket_out.py", "w")
braket_out.writelines(python_code)
braket_out.close()
