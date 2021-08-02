# pylint: skip-file

from tabulate import tabulate

from .aws_utils import BRAKET_PROVIDERS
from .google_utils import CIRQ_PROVIDERS
from .ibm_utils import QISKIT_PROVIDERS
from .ibm_utils import QiskitRunInput

SUPPORTED_VENDORS = {
    "AWS": BRAKET_PROVIDERS,
    "Google": CIRQ_PROVIDERS,
    "IBM": QISKIT_PROVIDERS,
}


def get_devices():
    """Prints all available devices, tabulated by provider and vendor."""
    device_list = []
    for vendor_key in SUPPORTED_VENDORS:
        for provider_key in SUPPORTED_VENDORS[vendor_key]:
            for device_key in SUPPORTED_VENDORS[vendor_key][provider_key]:
                device_list.append([vendor_key, provider_key, device_key])
    print(tabulate(device_list, headers=["Software Vendor", "Device Provider", "Device Name"]))
