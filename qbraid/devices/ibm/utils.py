from qiskit.providers.aer import AerSimulator, PulseSimulator
from qiskit import QuantumCircuit
from qiskit.pulse import Schedule
from typing import Union

QiskitRunInput = Union[QuantumCircuit, Schedule, list]

IBM_DEVICES = {
    "AerSimulator": AerSimulator(),
    "PulseSimulator": PulseSimulator(),
}

QISKIT_PROVIDERS = {
    "IBM": IBM_DEVICES,
}
