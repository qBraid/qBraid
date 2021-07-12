from typing import Union

from qiskit import QuantumCircuit
from qiskit.providers.aer import AerSimulator, PulseSimulator, QasmSimulator, \
    StatevectorSimulator, UnitarySimulator
from qiskit.providers.basicaer import QasmSimulatorPy, StatevectorSimulatorPy, UnitarySimulatorPy
from qiskit.pulse import Schedule

QiskitRunInput = Union[QuantumCircuit, Schedule, list]

IBM_DEVICES = {
    'AerSimulator': AerSimulator(),
    'PulseSimulator': PulseSimulator(),
    'QasmSimulator': QasmSimulator(),  # Aer.getbackend('qasm_simulator') also works
    'StatevectorSimulator': StatevectorSimulator(),
    'UnitarySimulator': UnitarySimulator(),
    'BasicAer StatevectorSimulator': StatevectorSimulatorPy(),
    'BasicAer UnitarySimulator': UnitarySimulatorPy(),
    'BasicAer QasmSimulator': QasmSimulatorPy(),
    'IBMQ Montreal': None,  # provider.get_backend('ibmq_armonk')
    'IBMQ Kolkata': None,  # provider.get_backend('ibmq_LOCATION')
    'IBMQ Mumbai': None,  # etc...
    'IBMQ Dublin': None,
    'IBMQ Manhattan': None,
    'IBMQ Brooklyn': None,
    'IBMQ Toronto': None,
    'IBMQ Sydney': None,
    'IBMQ Guadalupe': None,
    'IBMQ Casablanca': None,
    'IBMQ Nairobi': None,
    'IBMQ Santiago': None,
    'IBMQ Manila': None,
    'IBMQ Bogota': None,
    'IBMQ Jakarta': None,
    'IBMQ Quito': None,
    'IBMQ Belem': None,
    'IBMQ Yorktown': None,
    'IBMQ Lima': None,
    'IBMQ Armonk': None,
}

QISKIT_PROVIDERS = {
    'IBM': IBM_DEVICES,
}
