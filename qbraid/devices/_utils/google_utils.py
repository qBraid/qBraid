# pylint: skip-file

# from cirq_google import Sycamore, Sycamore23, Bristlecone, Foxtail
from cirq import Simulator, DensityMatrixSimulator

AQT_DEVICES = {
    "AQT": None,  # AQTSampler(url, access_token=access_token),
}

GOOGLE_DEVICES = {
    "Sycamore": None,  # Sycamore,
    "Sycamore23": None,  # Sycamore23,
    "Bristlecone": None,  # Bristlecone,
    "Foxtail": None,  # Foxtail,
    "local_simulator_default": Simulator(),
    "local_simulator_densitymatrix": DensityMatrixSimulator(),
}

IONQ_DEVICES = {
    "ionQdevice": None,  # ionq.Service(),
}

PASQAL_DEVICES = {
    "PasqalVirtualDevice": None,  # PasqalVirtualDevice,
}

CIRQ_PROVIDERS = {
    "AQT": AQT_DEVICES,
    "Google": GOOGLE_DEVICES,
    "IonQ": IONQ_DEVICES,
    "Pasqal": PASQAL_DEVICES,
}
