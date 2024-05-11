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
# Script to append a timestamp to the version number
# in the `_version.py` file if the version ends in "dev".
#
# This assists in distinguishing between different development builds 
# based on the time of their creation.
#
# Example Usage:
#   ./stamp_dev_version.sh
#
#   Given `_version.py` content: 
#   version = "1.0.0dev"
#
#   Output:
#   1.0.0dev20240809120000
################################################################################

set -e

# Constants
PROJECT_NAME="qbraid"
VERSION_FILE_PATH="_version.py"
TIMESTAMP_FORMAT="+%Y%m%d%H%M%S"

# Ensure we're at the root of the Git repository
repo_dir=$(git rev-parse --show-toplevel)

# Extract the actual version from the last line of the _version.py file
ACTUAL_VERSION=$(tail -n 1 "${repo_dir}/${PROJECT_NAME}/${VERSION_FILE_PATH}" | cut -d'"' -f 2)

# Append a timestamp if the version ends with "dev"
if [[ "${ACTUAL_VERSION}" == *"dev" ]]; then
  echo "${ACTUAL_VERSION}$(date "${TIMESTAMP_FORMAT}")"
else
  echo "Version doesn't end in dev: ${ACTUAL_VERSION}" >&2
  exit 1
fi
