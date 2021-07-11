from typing import Iterable, Union

from .circuit import Circuit


"""
A rudimentary module for drawing circuits.
"""


def _fix_length(output: Iterable[str]) -> str:
    """Fixes the length of the circuit.

    Args:
        output (str): The circuit that is to be printed out.

    Returns:
        str: Circuit that is realigned.

            Qubit 0: ---|H|-
            Qubit 1: -

            becomes:

            Qubit 0: ---|H|-
            Qubit 1: -------
    """
    for i, val in enumerate(output):
        if len(val) < len(max(output, key=len)):
            diff = len(max(output, key=len)) - len(val)
            output[i] += "-" * diff
    return output


def _draw_moment(
    output: Iterable[str], circuit: Union[Circuit, Iterable[Circuit]]
) -> list:
    """Draws a "|" to divide each moment.

    Args:
        output (str):  The iterable of strings that represent each circuit.
        circuit (Union[Circuit, Iterable[Circuit]]): The circuit that is to be drawn.

    Returns:
        list: The iterable of strings where the new moment is separated from the previous one.
    """
    for i in range(circuit.num_qubits):
        output[i] += "|"
    return output


def drawer(circuit: Circuit) -> None:
    """A rudimentary circuit drawer that prints out a string for each qubit.

        TODO: Draw the control and target qubit differently.
        TODO: Optimize currently O(n^3)...
    Args:
        circuit (Union[Circuit, Iterable[Circuit]]): The circuit that is to be drawn.
    """
    if isinstance(circuit, Circuit):
        output = [f"Qubit {str(i)}:" for i in range(circuit.num_qubits)]
        for moment in circuit.moments:
            output = _draw_moment(output, circuit)
            for instruction in moment.instructions:
                if instruction.gate.num_qubits == 1:
                    gate_content = "┤{}├".format(instruction.gate.name)
                    output[instruction.qubits[0]] += gate_content
                else:
                    # assuming only two qubit gates
                    gate_content = "┤{}├".format(instruction.gate.name)
                    output[instruction.qubits[0]] += gate_content
                    output[instruction.qubits[1]] += gate_content
            output = _fix_length(output)
        for i in output:
            print(i)
    else:
        raise TypeError(f"{circuit} is not a drawable object.")
