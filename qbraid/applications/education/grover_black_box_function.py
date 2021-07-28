# pylint: skip-file

from qiskit import QuantumCircuit
import numpy as np


def f0():
    """OR gate."""

    n = 4
    m = n  # ancilla qubits
    out_qubit = 2 * n + m - 1

    circ = QuantumCircuit(
        2 * n + m, 1
    )  # the first argument specifies that we are building a circuit
    # acting on 2n + m qubits.
    # The second argument specifies that we'll be measuring just 1 qubit.

    # first, we copy the input in the first n qubits to the second n qubits.
    for i in range(n):
        circ.cx(i, i + n)

    for i in [
        2 * n + k for k in range(m - 1)
    ]:  # apply an X gate to all ancilla qubits (i.e. we are initializing
        # them as |1>)
        circ.x(i)

    next_available_ancilla = 2 * n
    index = n
    for j in range(2):
        for k in range(n // 2 ** (j + 1)):
            circ.x(index + 2 * k)
            circ.x(index + 2 * k + 1)
            circ.ccx(index + 2 * k, index + 2 * k + 1, next_available_ancilla)
            next_available_ancilla += 1
        index += n // 2 ** j

    # finally a CNOT to the output qubit.
    circ.cx(out_qubit - 1, out_qubit)

    circ.x(out_qubit)

    # Undoing all gates, except the last.
    for j in list(reversed(range(int(np.log2(n))))):
        index -= n // 2 ** j
        for k in list(reversed(range(n // 2 ** (j + 1)))):
            next_available_ancilla -= 1
            circ.ccx(index + 2 * k, index + 2 * k + 1, next_available_ancilla)
            circ.x(index + 2 * k + 1)
            circ.x(index + 2 * k)

    for i in [
        2 * n + k for k in range(m - 1)
    ]:  # notice that we don't undo the x gate acting on the output qubit.
        circ.x(i)

    for i in range(n):
        circ.cx(i, i + n)

    circ.draw(output="mpl")


def f1():
    """OR gate."""

    n = 4
    m = n  # ancilla qubits
    out_qubit = 2 * n + m - 1

    circ = QuantumCircuit(
        2 * n + m, 1
    )  # the first argument specifies that we are building a circuit
    # acting on 2n + m qubits.
    # The second argument specifies that we'll be measuring just 1 qubit.

    # first, we copy the input in the first n qubits to the second n qubits.
    for i in range(n):
        circ.cx(i, i + n)

    for i in [
        2 * n + k for k in range(m - 1)
    ]:  # apply an X gate to all ancilla qubits (i.e. we are initializing
        # them as |1>)
        circ.x(i)

    next_available_ancilla = 2 * n
    index = n
    for j in range(2):
        for k in range(n // 2 ** (j + 1)):
            circ.x(index + 2 * k)
            circ.x(index + 2 * k + 1)
            circ.ccx(index + 2 * k, index + 2 * k + 1, next_available_ancilla)
            next_available_ancilla += 1
        index += n // 2 ** j

    # finally a CNOT to the output qubit.
    circ.cx(out_qubit - 1, out_qubit)

    circ.x(out_qubit)

    # Undoing all gates, except the last.
    for j in list(reversed(range(int(np.log2(n))))):
        index -= n // 2 ** j
        for k in list(reversed(range(n // 2 ** (j + 1)))):
            next_available_ancilla -= 1
            circ.ccx(index + 2 * k, index + 2 * k + 1, next_available_ancilla)
            circ.x(index + 2 * k + 1)
            circ.x(index + 2 * k)

    for i in [
        2 * n + k for k in range(m - 1)
    ]:  # notice that we don't undo the x gate acting on the output qubit.
        circ.x(i)

    for i in range(n):
        circ.cx(i, i + n)

    circ.draw(output="mpl")
