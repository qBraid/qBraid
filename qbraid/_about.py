# Copyright (C) 2024 qBraid
#
# This file is part of the qBraid-SDK
#
# The qBraid-SDK is free software released under the GNU General Public License v3
# or later. You can redistribute and/or modify it under the terms of the GPL v3.
# See the LICENSE file in the project root or <https://www.gnu.org/licenses/gpl-3.0.html>.
#
# THERE IS NO WARRANTY for the qBraid-SDK, as per Section 15 of the GPL v3.

"""
Information about qBraid and dependencies.

"""

import importlib.metadata
import platform
import re
from typing import Optional

from ._compat import check_warn_version_update
from ._version import __version__


def get_dependencies(
    package_name, exclude_extras: Optional[set[str]] = None
) -> tuple[list[str], dict[str, list[str]]]:
    """
    Extracts core and optional dependencies of a package using importlib.metadata.

    Args:
        package_name (str): Name of the package to analyze.
        exclude_extras (optional, set[str]): Optional set of extras to exclude from the analysis.

    Returns:
        Tuple containing two elements:
        - list[str]: Core dependencies without any extras.
        - dict[str, list[str]]: Dependencies categorized by their extras
    """
    dist = importlib.metadata.distribution(package_name)
    requires = dist.requires or []

    core_dependencies = []
    optional_dependencies = {}
    extras_regex = re.compile(r'^(.+?); extra == "([^"]+)"$')
    package_name_pattern = re.compile(r"^([^>=<\[\]]+)")

    exclude_extras = exclude_extras or set()

    for req in requires:
        req = req.strip()
        match = extras_regex.match(req)
        if match:
            dependency, extra = match.groups()
            if extra in exclude_extras:
                continue
            dependency = package_name_pattern.match(dependency.strip()).group(0)
            optional_dependencies.setdefault(extra, []).append(dependency)
        else:
            dependency = package_name_pattern.match(req).group(0)
            core_dependencies.append(dependency)

    return core_dependencies, optional_dependencies


def about() -> None:
    """Displays information about qBraid, core/optional packages, and Python
    version/platform information.
    """
    exclude_extras = {"test", "lint", "docs", "visualization"}
    core_packages, _ = get_dependencies("qbraid", exclude_extras=exclude_extras)

    optional_packages = [
        "qbraid-qir",
        "amazon-braket-sdk",
        "cirq-core",
        "pyquil",
        "pennylane",
        "pytket",
        "qiskit",
        "qiskit-ibm-runtime",
        "oqc-qcaas-client",
    ]

    dependencies = {}

    for package_name in core_packages + optional_packages:
        try:
            dependencies[package_name] = importlib.metadata.distribution(package_name).version
        except importlib.metadata.PackageNotFoundError:  # pragma: no cover
            continue

    core_dependencies = {
        pkg: version for pkg, version in dependencies.items() if pkg in core_packages
    }
    optional_dependencies = {
        pkg: version for pkg, version in dependencies.items() if pkg in optional_packages
    }

    about_str = (
        "\nqBraid-SDK: A platform-agnostic quantum runtime framework\n"
        "======================================================================\n"
        f"(C) 2024 qBraid Development Team (https://github.com/qBraid/qBraid)\n\n"
        f"qbraid:\t{__version__}\n\n"
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

    check_warn_version_update()  # pragma: no cover
