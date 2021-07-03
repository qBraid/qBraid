from typing import Union, Iterable

from .gate import Gate


class Instruction:
    def __init__(self, gate: Gate, qubits: Union[int, Iterable[int]]):

        if isinstance(qubits, int):
            self._qubits = [qubits]
        else:
            self._qubits = qubits

        self._gate = gate

    @property
    def gate(self):
        return self._gate

    @property
    def qubits(self):
        return self._qubits
