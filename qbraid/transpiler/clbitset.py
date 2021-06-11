from typing import Iterable, Union
from .clbit import Clbit

ClbitSetInput = Union["QiskitClassicalRegister", Iterable[Clbit], Iterable[str], Iterable[int]]
AppendInput = Union[Clbit, Iterable[Clbit]]


class ClbitSet:

    """
    A holder instance of ClbitSet

    Arguments:
        A definitive instance of ClbitSet is made by passing an iterable
        of the int or str names to define the clbits.

    Attributes:

    Methods:


    """

    def __init__(self, clbitset: ClbitSetInput = None):

        if clbitset:
            self.clbits = [Clbit(clbit) for clbit in clbitset]
        else:
            self.clbits = []

    def __len__(self):

        return len(self.clbits)

    def get_clbit_by_index(self, index: int):

        """
        search for the qBraid Clbit object in the ClbitSet that corresponds to
        to the passed qubit
        """

        for qbraid_clbit in self.clbits:
            if qbraid_clbit.index == index:
                assert type(qbraid_clbit) == Clbit
                return qbraid_clbit

    def get_clbit(self, target_clbit: ClbitSetInput):

        """same as get_qubit but for clbit"""

        for qbraid_clbit in self.clbits:
            if qbraid_clbit.clbit == target_clbit:
                assert type(qbraid_clbit) == Clbit
                return qbraid_clbit

    def get_clbits(self, targets: Iterable[ClbitSetInput]):
        return [self.get_clbit(clb) for clb in targets]

    def _append(self, clbit: Clbit):
        self.clbits.append(clbit)

    def append(self, clbits: AppendInput):
        if isinstance(clbits, Iterable):
            [self._append(clb) for clb in clbits]
        else:
            self._append(clbits)
