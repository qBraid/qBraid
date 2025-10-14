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
