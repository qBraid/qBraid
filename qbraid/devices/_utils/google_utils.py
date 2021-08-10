# pylint: skip-file

import os

# from cirq_google import Sycamore, Sycamore23, Bristlecone, Foxtail
from cirq import Simulator, DensityMatrixSimulator
from cirq.circuits import Circuit

cirq_run_input = Circuit

AQT_DEVICES = {
    # "AQT": AQTSampler(url, access_token=access_token),  # not available
}

GOOGLE_DEVICES = {
    # "Sycamore": Sycamore,        # not available
    # "Sycamore23": Sycamore23,    # not available
    # "Bristlecone": Bristlecone,  # not available
    # "Foxtail": Foxtail,          # not available
    "local_simulator_default": Simulator(),
    "local_simulator_densitymatrix": DensityMatrixSimulator(),
}

IONQ_DEVICES = {
    # "ionQdevice": ionq.Service(),  # not available
}

PASQAL_DEVICES = {
    # "PasqalVirtualDevice": PasqalVirtualDevice,  # not available
}

CIRQ_PROVIDERS = {
    "AQT": AQT_DEVICES,
    "Google": GOOGLE_DEVICES,
    "IonQ": IONQ_DEVICES,
    "Pasqal": PASQAL_DEVICES,
}
