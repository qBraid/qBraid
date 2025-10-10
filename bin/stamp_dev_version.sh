#!/bin/bash

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
#   version = "1.0.0.dev"
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
