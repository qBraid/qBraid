from .ibm.devices import _get_ibm_device
from .google.devices import _get_google_device
from .utils import get_vendor_name


def get_qbraid_device(device: str):

    # determine vendor
    if isinstance(device, str):
        vendor, device = device.split("_", 1)
    else:
        vendor = get_vendor_name(device)

    # get qBraid device object
    if vendor == "IBM":
        return _get_ibm_device(device)
    elif vendor == "Google":
        return _get_google_device(device)
    else:
        raise TypeError("Cannot execute on devices from vendor {} yet".format(vendor))
