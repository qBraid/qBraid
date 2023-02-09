"""
Module containing functions to convert between Cirq's circuit
representation and Qiskit's circuit representation.

"""
import cirq
import qiskit

from qbraid.interface import convert_to_contiguous
from qbraid.interface.qbraid_cirq.tools import _convert_to_line_qubits
from qbraid.transpiler.cirq_utils import from_qasm, to_qasm
from qbraid.transpiler.cirq_utils.custom_gates import _map_zpow_and_unroll


def to_qiskit(circuit: cirq.Circuit) -> qiskit.QuantumCircuit:
    """Returns a Qiskit circuit equivalent to the input Cirq circuit. Note
    that the output circuit registers may not match the input circuit
    registers.

    Args:
        circuit: Cirq circuit to convert to a Qiskit circuit.

    Returns:
        Qiskit.QuantumCircuit object equivalent to the input Cirq circuit.
    """
    contig_circuit = convert_to_contiguous(circuit, rev_qubits=True)
    compat_circuit = _map_zpow_and_unroll(contig_circuit)
    return qiskit.QuantumCircuit.from_qasm_str(to_qasm(compat_circuit))


def from_qiskit(circuit: qiskit.QuantumCircuit) -> cirq.Circuit:
    """Returns a Cirq circuit equivalent to the input Qiskit circuit.

    Args:
        circuit: Qiskit circuit to convert to a Cirq circuit.

    Returns:
        Cirq circuit representation equivalent to the input Qiskit circuit.
    """
    gate_defs = {}
    qasm_lst_out = []
    qasm_str = circuit.qasm()
    qasm_lst = qasm_str.split("\n")
    get_param = lambda x: x[x.index("(") + 1 : x.index(")")]
    for _, qasm_line in enumerate(qasm_lst):
        line_str = qasm_line
        line_args = line_str.split(" ")
        if line_args[0] == "gate":
            gate = line_args[1]
            qs = line_args[2].split(",")
            instr = line_str.split("{")[1].strip("}").strip()
            gate_defs[gate] = (qs, instr)
            try:
                param_var = get_param(gate)
                param_def = get_param(instr)
                match_gate = gate.replace(param_var, param_def)
                gate_defs[match_gate] = (qs, instr)
            except ValueError:
                pass
            line_str_out = "// " + line_str
        elif line_str[0:2] == "cu":
            cu_gate = line_args[0]
            q0, q1 = line_args[1].strip(";").split(",")
            params_lst = get_param(cu_gate).split(",")
            params = [float(x) for x in params_lst]
            theta, phi, lam, gamma = params
            line_str_out = "// CUGate\n"
            line_str_out = f"p({gamma}) {q0};\n"
            line_str_out += f"p({(lam+phi)/2}) {q0};\n"
            line_str_out += f"p({(lam-phi)/2}) {q1};\n"
            line_str_out += f"cx {q0},{q1};\n"
            line_str_out += f"u({-1*theta/2},0,{-1*(phi+lam)/2}) {q1};\n"
            line_str_out += f"cx {q0},{q1};\n"
            line_str_out += f"u({theta/2},{phi},0) {q1};\n"
        elif line_args[0] in gate_defs:
            qs, instr = gate_defs[line_args[0]]
            map_qs = line_args[1].strip(";").split(",")
            for i, qs_i in enumerate(qs):
                instr = instr.replace(qs_i, map_qs[i])
            line_str_out = instr
        else:
            line_str_out = line_str
        if line_str_out[0:2] != "//" and len(line_str_out) > 0:
            for g in gate_defs:
                line_lst_out = line_str_out.split(";")
                line_lst_out_copy = []
                for line_instr in line_lst_out:
                    line_args = line_instr.split(" ")
                    qasm_gate = line_args[0]
                    if g != qasm_gate:
                        try:
                            param = get_param(qasm_gate)
                            qasm_gate = qasm_gate.replace(param, "param0")
                            if g != qasm_gate:
                                qasm_gate = qasm_gate.replace("param0", "param0,param1")
                        except ValueError:
                            pass
                    if g == qasm_gate:
                        qs, instr = gate_defs[g]
                        map_qs = line_args[1].split(",")
                        for i, qs_i in enumerate(qs):
                            instr = instr.replace(qs_i, map_qs[i])
                        line_instr = instr
                    if len(line_instr) > 0:
                        line_lst_out_copy.append(line_instr)
                line_lst_out_strip = [x.strip() for x in line_lst_out_copy]
                line_str_out = ";".join(line_lst_out_strip) + ";"

        qasm_lst_out.append(line_str_out)

    qasm_str_def = "\n".join(qasm_lst_out)
    cirq_circuit = from_qasm(qasm_str_def)
    return _convert_to_line_qubits(cirq_circuit, rev_qubits=True)
