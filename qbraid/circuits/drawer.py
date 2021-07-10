from typing import Iterable, Union


from .circuit import Circuit
from .instruction import Instruction
from .update_rule import UpdateRule
from .moment import Moment

"""
A rudimentary module for drawing circuits.
"""


def _fix_length(output: str) -> str:
    for i in range(len(output)):
        if len(output[i]) < len(max(output, key=len)):
            diff = len(max(output, key=len)) - len(output[i])
            output[i] += "-" * diff
    return output


def _draw_moment(
    output: str, moment: Moment, circuit: Union[Circuit, Iterable[Circuit]]
) -> list:
    for i in range(circuit.num_qubits):
        output[i] += "|"
    return output


def drawer(circuit: Union[Circuit, Iterable[Circuit]]) -> None:
    """A rudimentary drawer"""
    output = [f"Qubit {str(i)}:" for i in range(circuit.num_qubits)]
    for moment in circuit.moments:
        output = _draw_moment(output, moment, circuit)
        for instruction in moment.instructions:
            if instruction.gate.num_qubits == 1:
                gate_content = "┤{}├".format(instruction.gate.name)
                output[instruction.qubits[0]] += gate_content
            else:
                # assuming only two qubit gates
                gate_content = "┤{}├".format(
                    instruction.gate.name, instruction.qubits[0]
                )
                output[instruction.qubits[0]] += gate_content
                output[instruction.qubits[1]] += gate_content
        output = _fix_length(output)
    for i in output:
        print(i)
