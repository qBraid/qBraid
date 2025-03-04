# Copyright (C) 2025 qBraid
#
# This file is part of the qBraid-SDK
#
# The qBraid-SDK is free software released under the GNU General Public License v3
# or later. You can redistribute and/or modify it under the terms of the GPL v3.
# See the LICENSE file in the project root or <https://www.gnu.org/licenses/gpl-3.0.html>.
#
# THERE IS NO WARRANTY for the qBraid-SDK, as per Section 15 of the GPL v3.

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
