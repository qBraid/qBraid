# pylint: skip-file

# from cirq_google import Sycamore, Sycamore23, Bristlecone, Foxtail
from cirq import DensityMatrixSimulator, Simulator

AQT_DEVICES = {
    # "AQT": AQTSampler(url, access_token=access_token),  # not available
}

GOOGLE_DEVICES = {
    # "Sycamore": Sycamore,        # not available
    # "Sycamore23": Sycamore23,    # not available
    # "Bristlecone": Bristlecone,  # not available
    # "Foxtail": Foxtail,          # not available
}

CIRQ_SIMULATORS = {
    "google_cirq_sparse_sim": Simulator(),
    "google_cirq_dm_sim": DensityMatrixSimulator(),
}

IONQ_DEVICES = {
    # "ionQdevice": ionq.Service(),  # not available
}

PASQAL_DEVICES = {
    # "PasqalVirtualDevice": PasqalVirtualDevice,  # not available
}

CIRQ_PROVIDERS = {
    "aqt": AQT_DEVICES,
    "google": GOOGLE_DEVICES,
    "cirq": CIRQ_SIMULATORS,
    "ionQ": IONQ_DEVICES,
    "pasqal": PASQAL_DEVICES,
}

GOOGLE_DEVICE_INFO = {
    "google_cirq_sparse_sim": ["Google", "Cirq Sparse Simulator", "--"],
    "google_cirq_dm_sim": ["Google", "Cirq Density Matrix Simulator", "--"],
}
