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
Update the CITATION.cff file with the new version and release date.
"""

import pathlib
import sys
from datetime import date

import yaml


def update_citation_cff(version: str) -> None:
    """Update the CITATION.cff file with the new version and release date."""
    root = pathlib.Path(__file__).parent.parent.resolve()
    citation_file = root / "CITATION.cff"

    with open(citation_file, "r", encoding="utf-8") as file:
        data = yaml.safe_load(file)

    data["version"] = version
    data["repository-artifact"] = f"https://github.com/qBraid/qBraid/releases/tag/v{version}"

    today = date.today()
    data["date-released"] = today.strftime("%Y-%m-%d")

    with open(citation_file, "w", encoding="utf-8") as file:
        yaml.dump(data, file, sort_keys=False)

    print(f"CITATION.cff updated with version {version} and release date {today}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python update_citation.py <new_version>")
        sys.exit(1)

    new_version = sys.argv[1]
    update_citation_cff(new_version)
