from .aws.device import BraketDeviceWrapper
from .google.device import CirqDeviceWrapper
from .ibm.device import QiskitDeviceWrapper
from .device import DeviceWrapper
from .exceptions import DeviceError
from tabulate import tabulate
from typing import Optional, Union

from .aws.utils import BRAKET_PROVIDERS
from .google.utils import CIRQ_PROVIDERS
from .ibm.utils import QISKIT_PROVIDERS

SUPPORTED_VENDORS = {
    'AWS': BRAKET_PROVIDERS,
    'Google': CIRQ_PROVIDERS,
    'IBM': QISKIT_PROVIDERS,
}


def device_wrapper(name: str, provider: str, vendor: Optional[str] = None, **fields) \
        -> DeviceWrapper:
    """Apply qbraid device wrapper to device from a supported device provider. If vendor is None,
    it is assumed that the vendor is the same as the provider. If the vendor is not the same as the
    provider, the vendor must be specified.

    Args:
        name (str): a quantum hardware device/simulator available through given `provider`
        provider (str): a quantum hardware device/simulator provider available through `vendor`
        vendor (Optional[str]): a quantum software vendor

    Returns:
        :class:`~qbraid.devices.device.DeviceWrapper`: a qbraid device wrapper object
    Raises:
        :class:`~qbraid.DeviceError`: If `vendor` is not a supported vendor.
    """
    if vendor is None:
        vendor = provider

    if vendor == "AWS":
        return BraketDeviceWrapper(name, provider, **fields)
    elif vendor == "Google":
        return CirqDeviceWrapper(name, provider, **fields)
    elif vendor == "IBM":
        return QiskitDeviceWrapper(name, provider, **fields)
    else:
        raise DeviceError("\"{}\" is not a supported vendor.".format(vendor))


def get_devices():
    """Prints all available devices, tabulated by provider and vendor."""
    device_list = []
    for vendor_key in SUPPORTED_VENDORS:
        for provider_key in SUPPORTED_VENDORS[vendor_key]:
            for device_key in SUPPORTED_VENDORS[vendor_key][provider_key]:
                device_list.append([vendor_key, provider_key, device_key])
    print(tabulate(device_list, headers=['Software Vendor', 'Device Provider', 'Device Name']))
