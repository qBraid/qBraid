from typing import Iterable


def get_package_name(obj):

    """Determine package of an object using the .__module__ method"""

    package_name = obj.__module__.split(".")[0]

    if package_name in ["qiskit", "cirq", "braket", "qbraid"]:
        return package_name
    else:
        print("Could not determine package for obj of type {}".format(type(obj)))
