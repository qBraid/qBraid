# Copyright 2025 qBraid
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

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
