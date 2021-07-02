from qiskit.providers.aer import AerSimulator, PulseSimulator

IBM_DEVICES = {
    'AerSimulator': AerSimulator,
    'PulseSimulator': PulseSimulator
}

IBM_PROVIDERS = {
    'IBM': IBM_DEVICES,
}

