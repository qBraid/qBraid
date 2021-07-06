import numpy as np
from typing import Iterable, Union

from .exceptions import CircuitError
from .instruction import Instruction
from .moment import Moment


def validate_qubit(op, num_qubits):
    if isinstance(op, Instruction):
        if max(op.qubits) <= num_qubits and np.all(np.array(op.qubits) >= 0):
            return True
        else:
            return False
    else:
        return True


def validate_operation(
    op: Union[
        Instruction,
        Moment,
    ],
    num_qubits,
) -> bool:
    from .circuit import Circuit

    if (
        isinstance(op, Instruction) or isinstance(op, Moment) or isinstance(op, Circuit)
    ) and validate_qubit(op, num_qubits):
        return True
    else:
        raise CircuitError(
            "Operation of type {} not appendable in circuit of {} qubits".format(
                type(op), num_qubits
            )
        )
