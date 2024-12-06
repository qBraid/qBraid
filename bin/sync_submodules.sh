#!/bin/bash

# Copyright (C) 2024 qBraid
#
# This file is part of the qBraid-SDK
#
# The qBraid-SDK is free software released under the GNU General Public License v3
# or later. You can redistribute and/or modify it under the terms of the GPL v3.
# See the LICENSE file in the project root or <https://www.gnu.org/licenses/gpl-3.0.html>.
#
# THERE IS NO WARRANTY for the qBraid-SDK, as per Section 15 of the GPL v3.

################################################################################
# Description:
# Synchronizes, initializes, and updates Git submodules in this repository.
#
# Usage:
#   ./sync_submodules.sh
################################################################################

REPO_ROOT=$(git rev-parse --show-toplevel)

cd "$REPO_ROOT" || { echo "Failed to navigate to repository root"; exit 1; }

git submodule sync
git submodule init
git submodule update --remote --recursive
git submodule update --remote --merge
