import numpy as np
from openfermion.ops import FermionOperator, InteractionOperator

from openfermion.transforms import (
    get_interaction_operator,
    get_fermion_operator,
    normal_ordered,
)

from qiskit.chemistry import FermionicOperator


def convert(fer_int_op, output_type="QISKIT"):
    """Convert the fermion_operator between the various types available.

    Args:
        fer_int_op: FermionicOperator class in qiskit-aqua or interactionoperator class
            in openfermion
        output_type (string): string for specifying the return package type for qubit_operator

    Returns:
        fermion_operator class in the requested package

    """
    if isinstance(fer_int_op, InteractionOperator):
        if output_type == "QISKIT":
            # OF_inter_oper = molecular_hamiltonian
            h1 = fer_int_op.one_body_tensor
            h2 = fer_int_op.two_body_tensor
            h2 = np.einsum("ikmj->ijkm", h2)
            fer_op_qiskit = FermionicOperator(h1, h2)
            fer_op_qiskit._convert_to_block_spins()
            return fer_op_qiskit
        elif output_type == "OPENFERMION":
            pass

    if isinstance(fer_int_op, FermionOperator):
        if output_type == "QISKIT":
            # OF_inter_oper = molecular_hamiltonian
            fer_int_op = normal_ordered(fer_int_op)
            int_op = get_interaction_operator(fer_int_op)
            h1 = int_op.one_body_tensor
            h2 = int_op.two_body_tensor
            h2 = np.einsum("ikmj->ijkm", h2)
            fer_op_qiskit = FermionicOperator(h1, h2)
            fer_op_qiskit._convert_to_block_spins()
            return fer_op_qiskit
        elif output_type == "OPENFERMION":
            pass

    elif isinstance(fer_int_op, FermionicOperator):
        if output_type == "OPENFERMION":
            fer_int_op._convert_to_interleaved_spins()
            h1 = fer_int_op.h1
            h2 = fer_int_op.h2
            h2 = np.einsum("ijkm->ikmj", h2)
            of_int_op = InteractionOperator(0.0, h1, h2)
            of_fer_op = get_fermion_operator(of_int_op)
            return of_fer_op

    else:
        raise TypeError("The input type is not valid")


if __name__ == "__main__":
    pass
