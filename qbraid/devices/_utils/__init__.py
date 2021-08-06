# pylint: skip-file

from tabulate import tabulate

from .aws_utils import (
    BRAKET_PROVIDERS,
    AWS_CONFIG_PROMPT,
)

from .google_utils import CIRQ_PROVIDERS
from .ibm_utils import QISKIT_PROVIDERS
from .ibm_utils import QiskitRunInput
from .user_config import set_config, validate_config

SUPPORTED_VENDORS = {
    "AWS": BRAKET_PROVIDERS,
    "Google": CIRQ_PROVIDERS,
    "IBM": QISKIT_PROVIDERS,
}

CONFIG_PROMPTS = {
    "AWS": AWS_CONFIG_PROMPT,
    "Google": None,
    "IBM": None,
}


def get_devices():
    """Prints all available devices, tabulated by provider and vendor."""
    device_list = []
    for vendor_key in SUPPORTED_VENDORS:
        for provider_key in SUPPORTED_VENDORS[vendor_key]:
            for device_key in SUPPORTED_VENDORS[vendor_key][provider_key]:
                device_list.append([vendor_key, provider_key, device_key])
    print(tabulate(device_list, headers=["Software Vendor", "Device Provider", "Device Name"]))
