from typing import Iterable, Union

from .moment import Moment
from .circuit import Circuit
from .qubit import Qubit
from .instruction import Instruction
from .gate import Gate


def validate_operation(op: Union[Instruction, Moment, Circuit,]) -> bool:
    if isinstance(op, Instruction) or isinstance(op, Moment) or isinstance(op, Circuit):
        return True
    else:
        raise TypeError("Operation of type {} not appendable".format(type(op)))
