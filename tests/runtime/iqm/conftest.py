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
Skip the IQM runtime tests when the ``iqm`` extra is not installed.

``qbraid.runtime.iqm`` imports ``iqm-client`` at module scope, so without the extra
these modules raise at collection rather than skipping.

"""
import pytest

pytest.importorskip("iqm.iqm_client", reason="iqm extra not installed")
