import numpy as np
from openfermion.ops import QubitOperator
from openfermion.utils import count_qubits
from qiskit.aqua.operators import WeightedPauliOperator
from qiskit.quantum_info import Pauli


def convert(qubit_operator, output_qo_type="QISKIT"):
    """Convert the qubit_operator between the various types available
    in
    Args:
        qubit_operator: in either qiskit-aqua or openfermion
        output_qo_type (string): string for specifying the return package type for
                                qubit_operator
    Returns:
        qubit_operator class in the requested package
    """
    if isinstance(qubit_operator, QubitOperator):
        if output_qo_type == "QISKIT":
            num_qubits = count_qubits(qubit_operator)
            output_qub_op = WeightedPauliOperator(paulis=[[0, Pauli.from_label("I" * num_qubits)]])
            for term, coeff in qubit_operator.terms.items():
                z = np.zeros(num_qubits)
                x = np.zeros(num_qubits)
                for gate in list(term):
                    if gate[1] == "X":
                        x[gate[0]] = 1
                    elif gate[1] == "Z":
                        z[gate[0]] = 1
                    elif gate[1] == "Y":
                        x[gate[0]] = 1
                        z[gate[0]] = 1
                output_qub_op += WeightedPauliOperator(paulis=[[coeff, Pauli(z=z, x=x)]])
            return output_qub_op
        elif output_qo_type == "OPENFERMION":
            pass

    elif isinstance(qubit_operator, WeightedPauliOperator):
        if output_qo_type == "OPENFERMION":
            num_qubits = qubit_operator.num_qubits
            output_qub_op = QubitOperator()
            for term in qubit_operator._paulis:
                coeff = term[0]
                wpo_pauli = term[1]

                # the _z and _x properties return a list of list [[True,False..]]
                # changed to get actual list using [0]
                z = wpo_pauli._z[0]
                x = wpo_pauli._x[0]
                of_term = []
                for i in range(num_qubits):
                    if x[i] and z[i]:
                        of_term.append((i, "Y"))
                    elif x[i]:
                        of_term.append((i, "X"))
                    elif z[i]:
                        of_term.append((i, "Z"))
                    else:
                        pass
                output_qub_op += QubitOperator(tuple(of_term), coeff)
            return output_qub_op
        elif output_qo_type == "PYQUIL":
            pass

    elif isinstance(qubit_operator, QubitOperator):
        pass
    else:
        raise TypeError("Input must be an one of the QubitOperators")
