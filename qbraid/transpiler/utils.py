from qbraid.exceptions import PackageError

supported_packages = {
    "cirq": ["braket", "qiskit"],
    "qiskit": ["braket", "cirq"],
    "braket": ["qiskit", "cirq"],
}


def get_package_name(obj):

    """Determine package of an object using the .__module__ method"""

    package_name = obj.__module__.split(".")[0]

    if package_name in ["qiskit", "cirq", "braket", "qbraid"]:
        return package_name
    else:
        raise PackageError(f"{package_name} is not a supported package.")
