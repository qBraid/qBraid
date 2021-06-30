from .exceptions import DeviceError


def get_vendors():
    return ["Google", "IBM", "IonQ", "Rigetti", "D-Wave"]


def get_devices(vendor: str = None):
    if vendor is None:
        return NotImplementedError
    elif vendor in get_vendors():
        return NotImplementedError
    else:
        raise DeviceError("{} is not a supported vendor.".format(vendor))
