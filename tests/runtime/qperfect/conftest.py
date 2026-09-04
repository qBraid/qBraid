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
Pytest configuration and shared fixtures for the QPerfect (MIMIQ) runtime tests.

The suite exercises real ``mimiqcircuits`` objects (``Circuit``, ``BitString``) and the
``qiskit -> mimiqcircuits`` transpiler edge, both of which require the optional ``qperfect`` extra
(``mimiqcircuits`` + ``mimiq-qiskit``). Skip the whole directory when it is unavailable. When it is
installed, the fixtures below provide a fully mocked MIMIQ connection (no network): the provider's
``connection`` is stubbed so ``connectToken`` is never called.
"""

from __future__ import annotations

import importlib.util

collect_ignore = []
if (
    importlib.util.find_spec("mimiqcircuits") is None
    or importlib.util.find_spec("mimiq_qiskit") is None
):
    collect_ignore = ["test_client.py", "test_provider.py", "test_device.py", "test_job.py"]
else:
    from unittest.mock import MagicMock

    import mimiqcircuits as mc
    import pytest

    from qbraid.runtime.qperfect import QPerfectProvider

    @pytest.fixture
    def mock_connection() -> MagicMock:
        """A fully mocked MIMIQ connection (no network).

        ``submit`` returns a fixed execution id; the nested ``.connection`` (the ``mimiqlink``
        layer) stubs ``isOpen`` (device health), ``requestInfo`` (job status, ``.status`` string),
        and cancel. Defaults describe an open connection and a completed (``DONE``) job.

        ``requestInfo().get`` follows ``RequestInfo.get`` in returning the caller's default for an
        absent key; a bare ``MagicMock`` would hand back a truthy mock for every field instead.
        """
        conn = MagicMock()
        conn.submit.return_value = "exec-1"
        conn.connection = MagicMock()
        conn.connection.isOpen.return_value = True
        info = MagicMock(status="DONE")
        info.get.side_effect = lambda key, default: default
        conn.connection.requestInfo.return_value = info
        return conn

    @pytest.fixture
    def fake_result() -> MagicMock:
        """A fake ``QCSResults`` whose ``histogram()`` maps ``BitString`` keys to counts.

        ``BitString([1, 0])`` renders ``to01() == "10"`` (qubit 0 first); the job reverses it to
        qBraid's little-endian ``"01"``.
        """
        result = MagicMock()
        result.histogram.return_value = {mc.BitString([1, 0]): 60, mc.BitString([0, 0]): 40}
        return result

    @pytest.fixture
    def provider(mock_connection) -> QPerfectProvider:
        """A provider whose network connection is stubbed out (no ``connectToken``)."""
        instance = QPerfectProvider(token="fake-token")
        instance._connection = mock_connection  # pylint: disable=protected-access
        return instance

    @pytest.fixture
    def device(provider):
        """The MIMIQ emulator device backed by the mocked connection."""
        return provider.get_device("mimiq-emulator")
