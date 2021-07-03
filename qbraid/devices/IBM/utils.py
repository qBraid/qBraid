from qiskit.providers.aer import AerSimulator, PulseSimulator

IBM_DEVICES = {
    'AerSimulator': AerSimulator,
    'PulseSimulator': PulseSimulator
}

QISKIT_PROVIDERS = {
    'IBM': IBM_DEVICES,
}

