# Copyright 2023 qBraid
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
Module for emitting and disabling warnings at top level.

"""
import warnings

import urllib3


def _warn_new_version(local: str, api: str) -> bool:
    """Returns True if you should warn user about updated package version,
    False otherwise."""

    v_local = int("".join(local.split(".")[:3]))
    v_api = int("".join(api.split(".")[:3]))

    if v_local < v_api:
        return True
    return False


def _check_version():
    """Emits UserWarning if updated package version exists in qBraid API
    compared to local copy."""

    # pylint: disable=import-outside-toplevel
    from ._version import __version__ as version_local
    from .api.session import QbraidSession

    session = QbraidSession()
    version_api = session.get("/public/lab/get-sdk-version", params={}).json()

    if _warn_new_version(version_local, version_api):
        warnings.warn(
            f"You are using qbraid version {version_local}; however, version {version_api} "
            "is available. To avoid compatibility issues, consider upgrading by uninstalling "
            "and reinstalling the qBraid-SDK environment.",
            UserWarning,
        )


warnings.filterwarnings("ignore", category=SyntaxWarning)
warnings.filterwarnings("ignore", category=UserWarning, message="Setuptools is replacing distutils")
warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", category=PendingDeprecationWarning)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

_check_version()
