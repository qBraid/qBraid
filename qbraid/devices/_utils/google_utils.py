# pylint: skip-file

from cirq_google import Sycamore, Sycamore23, Bristlecone, Foxtail

AQT_DEVICES = {
    'AQT': None,  # AQTSampler(url, access_token=access_token),
}

GOOGLE_DEVICES = {
    'Sycamore': Sycamore,
    'Sycamore23': Sycamore23,
    'Bristlecone': Bristlecone,
    'Foxtail': Foxtail
}

IONQ_DEVICES = {
    'ionQdevice': None,  # ionq.Service(),
}

PASQAL_DEVICES = {
    'PasqalVirtualDevice': None,  # PasqalVirtualDevice,
}

CIRQ_PROVIDERS = {
    'AQT': AQT_DEVICES,
    'Google': GOOGLE_DEVICES,
    'IonQ': IONQ_DEVICES,
    'Pasqal': PASQAL_DEVICES,
}