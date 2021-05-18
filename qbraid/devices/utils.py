from typing import Iterable


def get_vendor_name(device):

    name = device.__module__.split(".")[0]

    if name in ["qiskit", "cirq", "braket", "qbraid"]:
        if name == "qiskit":
            return "IBM"
        elif name == "cirq":
            return "Google"
        else:
            print("Cannot determine package type for {}".format(device.__module__))

    else:
        print("Could not determine package for obj of type {}".format(type(device)))
