# pylint: skip-file

from tabulate import tabulate

from .aws_utils import (
    BRAKET_PROVIDERS,
    AWS_CONFIG_PROMPT,
)

from .ibm_utils import (
    QISKIT_PROVIDERS,
    IBMQ_CONFIG_PROMPT,
    QiskitRunInput,
)

from .google_utils import (
    CIRQ_PROVIDERS,
)

from .user_config import set_config

SUPPORTED_VENDORS = {
    "AWS": BRAKET_PROVIDERS,
    "Google": CIRQ_PROVIDERS,
    "IBM": QISKIT_PROVIDERS,
}

CONFIG_PROMPTS = {
    "AWS": AWS_CONFIG_PROMPT,
    "Google": None,
    "IBM": IBMQ_CONFIG_PROMPT,
}


def update_config(vendor):
    """Update the config associated with given vendor

    Args:
        vendor (str): a supported vendor

    """
    prompt_lst = CONFIG_PROMPTS[vendor]
    for prompt in prompt_lst:
        set_config(*prompt, update=True)
    return 0


def valid_config(vendor):
    # TO DO: validate configuration for given vendor
    return False


def get_devices(provider=None, vendor=None, simulator=None):
    """Prints all available devices, tabulated by provider and vendor. The user may filter results
    according to a particular device provider, software vendor, or simulators/non-simulators.

    Args:
        provider (optional, str): the name of a device provider
        vendor (optional, str): the name of a software vendor
        simulator (optional, bool): whether or not to filter for simulators

    """
    device_list = []
    for vendor_key in SUPPORTED_VENDORS:
        if vendor is None or vendor == vendor_key:
            for provider_key in SUPPORTED_VENDORS[vendor_key]:
                if provider is None or provider == provider_key:
                    for device_key in SUPPORTED_VENDORS[vendor_key][provider_key]:
                        if simulator is None or simulator == (device_key.find("Simulator") != -1):
                            device_list.append([vendor_key, provider_key, device_key])
    if len(device_list) == 0:
        print("No devices found matching given criteria.")
    else:
        print(tabulate(device_list, headers=["Software Vendor", "Device Provider", "Device Name"]))
