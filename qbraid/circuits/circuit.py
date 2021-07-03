from typing import Union, Iterable

from .instruction import Instruction
from .moment import Moment
from .qubit import Qubit
from .utils import validate_operation


class Circuit:

    """
    Circuit class for qBraid quantum circuit objects.
    """

    def __init__(self, num_qubits, name: str = None, update_rule=None):

        self._qubits = [Qubit(i) for i in range(num_qubits)]
        self._moments = []
        self.name = None

    @property
    def num_qubits(self):
        return len(self._qubits)

    @property
    def num_gates(self):
        raise NotImplementedError

    @property
    def moments(self):
        return self._moments

    @property
    def instructions(self):

        instructions_list = []
        for moment in self._moments:
            instructions_list.append(moment.instructions)

        return instructions_list

    def _append(self, moments: Union[Moment, Iterable[Moment]]):

        if isinstance(moments, Moment):
            moments = [moments]

        # validate moment
        for moment in moments:
            if max(moment.qubits) > self.num_qubits:
                raise TypeError  # should be CircuitError('Index exceeds number of qubits in circuit')
        self._moments.extend(moments)

    def _append_circuit(self, operation, mapping: Union[list, dict]) -> None:

        """this is for adding subroutines to circuits. so if we have a 3-qubit subroutine,
        the user should specify [2,4,5], implying that qubit 0 on the subroutine is mapped
        to qubit 2 on the circuit, qubit 1 on the subroutine maps to qubit 4 on the circuit, etc.

        the user should also be able to specify directly as a dict:
            {0:2,1:4,5:5}

        """

        # TO DO validate mapping
        raise NotImplementedError

    def append(
        self,
        operation: Union[Instruction, Moment, Iterable[Instruction], Iterable[Moment]],
        mapping: Union[list, dict] = None,
        update_rule=None,
    ) -> None:

        """
        Add an operation (moment or instruction) to the circuit.

        TO DO: rules
        """

        # TO DO validate instruction given from user (check if qubit indices exceed highest qubit circuit)

        # TO DO define various update rules, for now, go with NEW_then_earliest

        if isinstance(operation, Circuit):
            self._append_circuit(operation, mapping)
        if isinstance(operation, Iterable):
            for op in operation.moments:
                self._append(op)
        elif isinstance(operation, Iterable):
            for op in operation:
                self._append(op)
        else:
            self._append(operation)

    def __len__(self):
        raise NotImplementedError

    def __str__(self):
        print(f"Circuit with {self.num_qubits} and {self.num_gates}")
