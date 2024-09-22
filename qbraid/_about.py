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
import datetime
import importlib.metadata
import platform
import re
from typing import Optional

from qbraid_core._compat import check_version

from ._version import __version__


def get_dependencies(
    package_name, exclude_extras: Optional[set[str]] = None
) -> tuple[set[str], dict[str, set[str]]]:
    """
    Extracts core and optional dependencies of a package using importlib.metadata.

    Args:
        package_name (str): Name of the package to analyze.
        exclude_extras (optional, set[str]): Optional set of extras to exclude from the analysis.

    Returns:
        Tuple containing two elements:
        - set[str]: Core dependencies without any extras.
        - dict[str, set[str]]: Dependencies categorized by their extras
    """
    dist = importlib.metadata.distribution(package_name)
    requires = dist.requires or []

    core_dependencies = set()
    optional_dependencies = {}
    extras_regex = re.compile(r'^(.+?); extra == "([^"]+)"$')
    package_name_pattern = re.compile(r"^([^>=<\[\]]+)")

    exclude_extras = exclude_extras or set()

    for req in requires:
        req = req.strip()
        match = extras_regex.match(req)
        if match:
            dependency, extra = match.groups()
            if extra not in exclude_extras:
                dependency = package_name_pattern.match(dependency.strip()).group(0)
                if extra in optional_dependencies:
                    extras: set[str] = optional_dependencies[extra]
                    extras.add(dependency)
                    optional_dependencies[extra] = extras
                else:
                    optional_dependencies[extra] = {dependency}
        else:
            dependency = package_name_pattern.match(req).group(0)
            core_dependencies.add(dependency)

    return core_dependencies, optional_dependencies


def about() -> None:
    """
    Displays information about the qBraid-SDK including the installed versions
    of its core and optional dependencies, as well as the Python version and
    operating platform on which it is running.
    """
    check_version("qbraid")
    exclude_extras = {"test", "lint", "docs"}
    core_packages, extras = get_dependencies("qbraid", exclude_extras=exclude_extras)
    optional_packages = {item for subset in extras.values() for item in subset}
    all_packages = core_packages | optional_packages

    core_dependencies = {}
    optional_dependencies = {}

    for pkg in sorted(all_packages):
        try:
            version = importlib.metadata.distribution(pkg).version
            if pkg in core_packages:
                core_dependencies[pkg] = version
            if pkg in optional_packages:
                optional_dependencies[pkg] = version
        except importlib.metadata.PackageNotFoundError:
            continue

    current_year = datetime.datetime.now().year

    about_str = (
        "\nqBraid-SDK: A platform-agnostic quantum runtime framework\n"
        "=========================================================\n"
        f"(C) {current_year} qBraid Development Team (https://sdk.qbraid.com)\n\n"
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
