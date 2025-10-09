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

"""
Unit tests for remote job submissions to the NEC Vector Annealer using the QbraidProvider.

"""
import pytest
from qbraid_core import QbraidSession

from qbraid import QbraidJob, QbraidProvider
from qbraid._logging import logger
from qbraid.runtime import DeviceStatus
from qbraid.runtime.native.result import NECVectorAnnealerResultData
from qbraid.runtime.schemas import QuboSolveParams


def has_access() -> bool:
    """Check if the user has access to the NEC Vector Annealer."""
    try:
        session = QbraidSession()

        user_data = session.get_user()
        permissions_nodes = user_data["permissionsNodes"]
        return "nec.annealer" in permissions_nodes
    except Exception as err:  # pylint: disable=broad-exception-caught
        logger.error(err)

    return False


@pytest.mark.remote
def test_submit_qubo_job_to_nec_vector_annealer():
    """Test submitting a QUBO job to the NEC Vector Annealer."""
    pyqubo = pytest.importorskip("pyqubo", reason="pyqubo is not installed")

    if not has_access():
        pytest.skip("User does not have access to the NEC Vector Annealer")

    s1, s2, s3, s4 = [pyqubo.Spin(f"s{i}") for i in range(1, 5)]
    H = (4 * s1 + 2 * s2 + 7 * s3 + s4) ** 2
    model = H.compile()
    qubo, offset = model.to_qubo()

    params = QuboSolveParams(offset=offset)

    provider = QbraidProvider()

    device = provider.get_device("nec_vector_annealer")

    if device.status() != DeviceStatus.ONLINE:
        pytest.skip("NEC Vector Annealer is not online")

    job: QbraidJob = device.run(qubo, params=params)

    # pylint: disable=no-member
    job.wait_for_final_state()
    result = job.result()
    # pylint: enable=no-member

    result_data = result.data
    assert isinstance(result_data, NECVectorAnnealerResultData)

    if result.success:
        assert result_data.num_solutions == len(result_data.solutions) == 1

        solution = result_data.solutions[0]
        assert isinstance(solution, dict)
        assert {"spin", "energy"}.issubset(solution.keys())

        spin: dict = solution["spin"]
        assert len(spin) == 4
        assert set(spin.keys()) == {"s1", "s2", "s3", "s4"}
        assert sum(spin.values()) > 0
        assert solution["energy"] == 0

    else:
        assert result.details["statusText"] == "Failed to authenticate with NEC server"
