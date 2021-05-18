from .braket.circuit import BraketCircuitWrapper
from .cirq.circuit import CirqCircuitWrapper
from .qiskit.circuit import QiskitCircuitWrapper
from .utils import get_package_name


def qbraid_wrapper(circuit):

    """Apply qbraid wrapper to a circuit-type object from a supported packasge.
    currently only works for "circuit" objects, but should probably also work
    for gates, instructions, etc."""

    package = get_package_name(circuit)

    if package == "qiskit":
        return QiskitCircuitWrapper(circuit)
    elif package == "cirq":
        return CirqCircuitWrapper(circuit)
    elif package == "braket":
        return BraketCircuitWrapper(circuit)
    else:
        print("Error: pacakge type not supported")
