from qbraid.exceptions import PackageError


def get_package_name(obj):

    """Determine package of an object using the .__module__ method"""

    package_name = obj.__module__.split(".")[0]

    if package_name in ["qiskit", "cirq", "braket", "qbraid"]:
        return package_name
    else:
        raise PackageError(str(package_name))
