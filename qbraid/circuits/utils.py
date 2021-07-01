from typing import Iterable, Union

from .instruction import Instruction
from .moment import Moment


def validate_operation(op: Union[Instruction, Moment,]) -> bool:
    from .circuit import Circuit
    if isinstance(op, Instruction) or isinstance(op, Moment) or isinstance(op, Circuit):
        return True
    else:
        raise TypeError("Operation of type {} not appendable".format(type(op)))
