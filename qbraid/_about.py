# Copyright (C) 2024 qBraid
#
# This file is part of the qBraid-SDK
#
# The qBraid-SDK is free software released under the GNU General Public License v3
# or later. You can redistribute and/or modify it under the terms of the GPL v3.
# See the LICENSE file in the project root or <https://www.gnu.org/licenses/gpl-3.0.html>.
#
# THERE IS NO WARRANTY for the qBraid-SDK, as per Section 15 of the GPL v3.

"""Information about qBraid and dependencies."""

from ._compat import check_warn_version_update


def about() -> None:
    """Displays information about qBraid, core/optional packages, and Python
    version/platform information.
    """
    # pylint: disable=import-outside-toplevel
    import platform

    from numpy import __version__ as numpy_version
    from openqasm3 import __version__ as openqasm3_version
    from qbraid_core import __version__ as qbraid_core_version
    from rustworkx import __version__ as rustworkx_version  # pylint: disable=no-name-in-module

    from ._version import __version__ as qbraid_version

    # Core dependencies
    core_dependencies = {
        "rustworkx": rustworkx_version,
        "openqasm3": openqasm3_version,
        "numpy": numpy_version,
        "qbraid_core": qbraid_core_version,
    }

    # Optional dependencies
    optional_packages = {
        "qbraid_qir": "qbraid_qir",
        "braket": "braket._sdk",
        "cirq": "cirq",
        "pyquil": "pyquil",
        "pennylane": "pennylane",
        "pytket": "pytket",
        "qiskit": "qiskit",
        "qiskit_ibm_runtime": "qiskit_ibm_runtime",
    }

    check_warn_version = False
    optional_dependencies = {}
    for package_name, import_path in optional_packages.items():
        try:
            package = __import__(import_path, fromlist=[""])
            optional_dependencies[package_name] = package.__version__
            check_warn_version = check_warn_version or package_name == "qbraid_core"
        except ImportError:  # pragma: no cover
            continue

    about_str = (
        "\nqBraid-SDK: A platform-agnostic quantum runtime framework\n"
        "======================================================================\n"
        f"(C) 2024 qBraid Development Team (https://github.com/qBraid/qBraid)\n\n"
        f"qbraid:\t{qbraid_version}\n\n"
        "Core Dependencies\n"
        "-----------------\n"
        + "\n".join([f"{k}: {v}" for k, v in core_dependencies.items()])
        + "\n\n"
        "Optional Dependencies\n"
        "---------------------\n"
    )

    if optional_dependencies:
        about_str += "\n".join([f"{k}: {v}" for k, v in optional_dependencies.items()])
    else:
        about_str += "None"

    about_str += (
        f"\n\nPython: {platform.python_version()}\n"
        f"Platform: {platform.system()} ({platform.machine()})"
    )
    print(about_str)

    if check_warn_version:
        check_warn_version_update()  # pragma: no cover
