# Copyright 2026 qBraid
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
Pytest configuration for the AQT runtime tests.

These tests exercise real ``aqt_connector`` pydantic models and the ``qiskit -> aqt`` transpiler
edge, both of which require the optional ``aqt-connector`` dependency (the ``aqt`` extra). That
package conflicts with ``pasqal-cloud`` (on ``auth0-python``) so it is not installed in the main
test environment; skip the whole directory when it is unavailable.
"""

import importlib.util

collect_ignore = []
if importlib.util.find_spec("aqt_connector") is None:
    collect_ignore = ["test_aqt_runtime.py"]
