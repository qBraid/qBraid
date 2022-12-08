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
    for _, qasm_line in enumerate(qasm_lst):
        line_str = qasm_line
        line_args = line_str.split(" ")
        if line_args[0] == "gate":
            gate = line_args[1]
            qs = line_args[2].split(",")
            instr = line_str.split("{")[1].strip("}").strip()
            gate_defs[gate] = (qs, instr)
            line_str_out = "// " + line_str
        elif line_args[0] in gate_defs:
            qs, instr = gate_defs[line_args[0]]
            map_qs = line_args[1].strip(";").split(",")
            for i, qs_i in enumerate(qs):
                instr = instr.replace(qs_i, map_qs[i])
            line_str_out = instr
        else:
            line_str_out = line_str
        qasm_lst_out.append(line_str_out)
    qasm_str_def = "\n".join(qasm_lst_out)
    cirq_circuit = from_qasm(qasm_str_def)
    return _convert_to_line_qubits(cirq_circuit, rev_qubits=True)
