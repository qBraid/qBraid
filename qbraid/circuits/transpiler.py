from .utils import get_package_name
from .circuit import QiskitCircuitWrapper, CirqCircuitWrapper, BraketCircuitWrapper

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
