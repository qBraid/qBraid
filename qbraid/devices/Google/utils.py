from cirq_google import Sycamore, Sycamore23

AQT_DEVICES = {}

GOOGLE_DEVICES = {
    'Sycamore': Sycamore,
    'Sycamore23': Sycamore23,
}

IONQ_DEVICES = {}

PASQAL_DEVICES = {}

GOOGLE_PROVIDERS = {
    'AQT': AQT_DEVICES,
    'Google': GOOGLE_DEVICES,
    'IonQ': IONQ_DEVICES,
    'Pasqal': PASQAL_DEVICES,
}
