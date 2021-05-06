from .utils import get_package_name

from .qiskit.circuit import QiskitCircuitWrapper
from .cirq.circuit import CirqCircuitWrapper
from .braket.circuit import BraketCircuitWrapper

def qbraid_wrapper(circuit):
    
    package = get_package_name(circuit)
    
    if package == 'qiskit':
        return QiskitCircuitWrapper(circuit)
    elif package == 'cirq':
        return CirqCircuitWrapper(circuit)
    elif package == 'braket':
        return BraketCircuitWrapper(circuit)
    else:
        print("Error: pacakge type not supported")
