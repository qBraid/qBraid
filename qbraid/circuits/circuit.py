from typing import Union, Iterable

from .update_rule import UpdateRule
from .instruction import Instruction
from .moment import Moment
from .qubit import Qubit
from .utils import validate_operation
from .exceptions import CircuitError


class Circuit:

    """
    Circuit class for qBraid quantum circuit objects.
    Args:
    TODO
    """

    def __init__(
        self,
        num_qubits,
        name: str = None,
        update_rule: UpdateRule = UpdateRule.NEW_THEN_INLINE,
    ):
        self._qubits = [Qubit(i) for i in range(num_qubits)]
        self._moments: Iterable[Moment] = []  # list of moments
        self.name = name
        self.update_rule = update_rule

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
                raise CircuitError(
                    "Index {} exceeds number of qubits {} in circuit".format(
                        moment.qubits, self.num_qubits
                    )
                )
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

    def update(self, operation, update_rule, index=0) -> int:
        # takes in both moment and instructions
        # index used for moments
        # recursively call update after changing new_then_inline to in_line
        # single instructions, flesh it out here, then move to update_rule function
        if isinstance(operation, Instruction):
            if update_rule is UpdateRule.NEW_THEN_INLINE:
                if self._moments[-1].instructions is None:
                    self._moments[-1].append(operation)
                # create a new moment for first operation
                new_moment = Moment(
                    index=len(self._moments) + 1, instructions=[operation]
                )
                self._moments.append(new_moment)
                # update_rule changes to INLINE
                update_rule = UpdateRule.INLINE
                # call update function with updated rule.
                self.update(
                    operation, update_rule=update_rule,
                )
            elif update_rule is UpdateRule.INLINE:
                curr_moment = self._moments[-1]
                if curr_moment.appendable(operation):
                    curr_moment.append(operation)
                else:
                    # create a new moment
                    new_moment = Moment(
                        index=len(self._moments) + 1, instructions=[operation]
                    )
                    self._moments.append(new_moment)
                    # call update rule again

            elif update_rule is UpdateRule.NEW:
                # create a new moment every time append is called
                new_moment = Moment(
                    index=len(self._moments) + 1, instructions=[operation]
                )
                self._moments.append(new_moment)
        elif isinstance(operation, Moment):
            # moments don't need a strategy. Need to be added at the desired index.
            self.moments.insert(operation._index, operation)
        return NotImplementedError

    def append(
        self,
        operation: Union[Instruction, Moment, Iterable[Instruction], Iterable[Moment]],
        mapping: Union[list, dict] = None,
        update_rule: UpdateRule = None,
    ) -> None:
        """
        Appends an operation (moment or instruction) to the circuit.
        Args:
            operation: The moment/instruction or iterable of moment/instructions to append.
            strategy: How to pick/create the moment to put operations into.
        TODO: rules
        """

        # TODO: validate instruction given from user (check if qubit indices exceed highest qubit circuit)

        # TODO: define various update rules, for now, go with NEW_then_inline
        if operation is None:
            raise TypeError(
                "Operation of type {} not appendable".format(type(operation))
            )  # redundant
        if update_rule is None:
            update_rule = self.update_rule
        if not self._moments:
            # initialize a new moment
            new_moment = Moment(index=len(self._moments))
            self._moments.append(new_moment)

        # iterable
        if isinstance(operation, Iterable):
            for op in operation:
                # use utils validate ope
                if isinstance(op, Instruction):
                    # porbably best to make a function
                    self._append(op)
                elif isinstance(op, Moment):
                    self._append(op)
                elif isinstance(op, Circuit):
                    self._append(op)
                else:
                    raise TypeError(
                        "Operation of type {} not appendable".format(type(operation))
                    )
        elif isinstance(operation, Circuit):
            # develop appending strategy for an entire circuit.
            self._append_circuit(operation, mapping)
        else:
            # make operation into interable and attempt to append.
            self.append(operation=[operation], mapping=mapping, update_rule=update_rule)

    def __len__(self):
        return len(self._moments)

    def __str__(self):
        print(f"Circuit with {self.num_qubits} and {self.num_gates}")
