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
Script to bump the major, minor, or patch version in _version.py

"""
import pathlib
import sys

from qbraid_core.system.versions import bump_version, get_latest_package_version


def update_version_file(version_file: pathlib.Path, new_version: str) -> None:
    """Bump the semantic version in the _version.py file."""
    content = version_file.read_text()

    updated_content = ""
    for line in content.splitlines():
        if line.startswith("__version__"):
            updated_content += f'__version__ = "{new_version}"\n'
        else:
            updated_content += line + "\n"

    version_file.write_text(updated_content)


if __name__ == "__main__":

    bump_type = sys.argv[1]

    package_name = "qbraid"

    root = pathlib.Path(__file__).parent.parent.resolve()
    version_path = root / package_name / "_version.py"

    current_version = get_latest_package_version(package_name)
    bumped_version = bump_version(current_version, bump_type)
    update_version_file(version_path, bumped_version)
    print(bumped_version)
