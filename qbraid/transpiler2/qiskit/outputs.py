from qiskit import QuantumCircuit, ClassicalRegister, QuantumRegister
from qiskit.circuit import Instruction as QiskitInstruction
from qiskit.circuit.measure import Measure as QiskitMeasure
from qiskit.circuit.quantumregister import Qubit

from typing import Tuple
from ..parameter import ParamID
from .utils import create_qiskit_gate, qiskit_gates


def circuit_to_qiskit(cw, auto_measure=False, output_mapping=None) -> QuantumCircuit:

    qreg = QuantumRegister(cw.num_qubits)
    output_mapping = {index: Qubit(qreg, index) for index in range(len(qreg))}

    # get instruction data to intermediate format
    # (will eventually include combing through moments)
    data = []
    measurement_qubit_indices = set()
    for instruction in cw.instructions:
        gate, qubits, measurement_qubits = instruction.transpile("qiskit", output_mapping)
        data.append((gate, qubits, measurement_qubits))
        measurement_qubit_indices.update(measurement_qubits)

    # determine the length of the classical register and initialize
    if auto_measure:
        creg = ClassicalRegister(len(cw.num_qubits))
    elif len(measurement_qubit_indices) == 0:
        creg = None
    else:
        creg = ClassicalRegister(len(measurement_qubit_indices))
        # store how a qubit id maps to a clbit for the user
        clbit_mapping = {qubit: index for index, qubit in enumerate(measurement_qubit_indices)}

    if creg:
        output_circ = QuantumCircuit(qreg, creg, name="qBraid_transpiler_output")
    else:
        output_circ = QuantumCircuit(qreg, name="qBraid_transpiler_output")

    # add instructions to circuit
    for gate, qubits, measurement_qubits in data:
        clbits = None if not measurement_qubits else [clbit_mapping[q] for q in measurement_qubits]
        output_circ.append(gate, qubits, clbits)

    # auto measure
    if auto_measure:
        raise NotImplementedError

    return output_circ


def instruction_to_qiskit(
    iw, output_qubit_mapping, output_param_mapping=None
) -> Tuple[QiskitInstruction, list, list]:

    gate = iw.gate.transpile("qiskit", output_param_mapping)
    qubits = [output_qubit_mapping[q] for q in iw.qubits]

    if isinstance(gate, QiskitMeasure):
        return gate, qubits, iw.qubits
    else:
        return gate, qubits, []


def gate_to_qiskit(gw, output_param_mapping):

    """Create qiskit gate from a qbraid gate wrapper object."""

    qiskit_params = gw.params.copy()
    for i, param in enumerate(qiskit_params):
        if isinstance(param, ParamID):
            qiskit_params[i] = output_param_mapping[param]

    data = {
        "type": gw._gate_type,
        "matrix": gw.matrix,
        "name": gw.name,
        "params": qiskit_params,
    }

    if gw._gate_type in qiskit_gates.keys():
        gw._outputs["qiskit"] = create_qiskit_gate(data)

    elif gw.base_gate:
        gw._outputs["qiskit"] = gw.base_gate.transpile("qiskit").control(gw.num_controls)

    elif not (gw.matrix is None):
        data["type"] = "Unitary"
        gw._outputs["qiskit"] = create_qiskit_gate(data)

    return create_qiskit_gate(data)
