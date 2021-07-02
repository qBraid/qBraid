from .aws.device import AWSDeviceWrapper
from .google.device import GoogleDeviceWrapper
from .ibm.device import IBMDeviceWrapper
from .device import DeviceWrapper
from .exceptions import DeviceError
from tabulate import tabulate

from .aws import AWS_PROVIDERS
from .google import GOOGLE_PROVIDERS
from .ibm import IBM_PROVIDERS

SUPPORTED_VENDORS = {
    'AWS': AWS_PROVIDERS,
    'Google': GOOGLE_PROVIDERS,
    'IBM': IBM_PROVIDERS,
}


def device_wrapper(vendor: str, provider: str, device: str, **fields) -> DeviceWrapper:
    """Apply qbraid device wrapper to device from a supported device provider.

    Args:
        vendor (str): a quantum software vendor
        provider (str): a quantum hardware device/simulator provider available through `vendor`
        device (str): a quantum hardware device/simulator available through given `provider`
    Returns:
        :class:`~qbraid.devices.device.DeviceWrapper`: a qbraid device wrapper object
    Raises:
        :class:`~qbraid.DeviceError`: If `vendor` is not a supported vendor.
    """

    if vendor == "AWS":
        return AWSDeviceWrapper(device, provider, **fields)
    elif vendor == "Google":
        return GoogleDeviceWrapper(device, provider, **fields)
    elif vendor == "IBM":
        return IBMDeviceWrapper(device, provider, **fields)
    else:
        raise DeviceError("{} is not a supported quantum software vendor.".format(vendor))


def get_devices():
    """Prints all available devices, tabulated by provider and vendor."""
    device_list = []
    for vendor_key in SUPPORTED_VENDORS:
        for provider_key in SUPPORTED_VENDORS[vendor_key]:
            for device_key in SUPPORTED_VENDORS[vendor_key][provider_key]:
                device_list.append([vendor_key, provider_key, device_key])
    print(tabulate(device_list, headers=['Software Vendor', 'Device Provider', 'Device Name']))
