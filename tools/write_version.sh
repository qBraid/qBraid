#!/bin/bash

# Copyright (C) 2023 qBraid
#
# This file is part of the qBraid-SDK
#
# The qBraid-SDK is free software released under the GNU General Public License v3
# or later. You can redistribute and/or modify it under the terms of the GPL v3.
# See the LICENSE file in the project root or <https://www.gnu.org/licenses/gpl-3.0.html>.
#
# THERE IS NO WARRANTY for the qBraid-SDK, as per Section 15 of the GPL v3.

set -e

DEV_VERSION="${1}"
OUT_DIR="${2}"

# Constants
REPO_DIR=$(git rev-parse --show-toplevel)
VERSION_FILE="${REPO_DIR}/qbraid/_version.py"
TMP_BRANCH="tmp_build_branch_$(date "+%Y%m%d%H%M%S")"

# Create and checkout temporary branch
git checkout -b "${TMP_BRANCH}"

echo '__version__ = "'"${DEV_VERSION}"'"' > "${VERSION_FILE}"

python -m build --outdir "${OUT_DIR}"

git checkout -
git branch -D "${TMP_BRANCH}"