# pylint: skip-file

# from cirq_google import Sycamore, Sycamore23, Bristlecone, Foxtail
from cirq import DensityMatrixSimulator, Simulator

GOOGLE_DEVICES = {
    "google_cirq_dm_sim": DensityMatrixSimulator(),
    "google_cirq_sparse_sim": Simulator(),
    # "google_bristlecone": Bristlecone,
    # "google_sycamore": Sycamore,
    # "google_sycamore23": Sycamore23,
    # "google_foxtail": Foxtail,
    # "google_aqt_sampler": AQTSampler(url, access_token=access_token),
    # "google_ionq": ionq.Service(),
    # "google_pasqal_virtual_device": PasqalVirtualDevice,
}
