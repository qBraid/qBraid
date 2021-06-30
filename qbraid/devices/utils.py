from typing import Union
from .exceptions import DeviceError


def get_providers():
    return ["AWS", "Google", "IBM", "IonQ", "Rigetti", "D-Wave"]


def get_devices(provider: str = None) -> Union[dict, list]:
    """Get all available devices from given `provider` or from all providers.

    Args:
        provider (str): a quantum device provider, see :func:`~qbraid.get_providers`

    Returns:
        list[str]
            If `provider` is not None: a list of available devices from given `provider`
        dict[str, list[str]]:
            If `provider` is None: a dictionary where each key is a provider from
            :func:`~qbraid.get_providers`, and each value is a list containing the corresponding
            available devices

    Raises:
        :class:`~qbraid.DeviceError`: If `provider` not in :func:`~qbraid.get_providers`
    """
    if provider is None:
        raise NotImplementedError
    elif provider in get_providers():
        raise NotImplementedError
    else:
        raise DeviceError("{} is not a supported provider.".format(provider))
