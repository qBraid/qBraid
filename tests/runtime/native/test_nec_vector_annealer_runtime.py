# Copyright (C) 2024 qBraid
#
# This file is part of the qBraid-SDK
#
# The qBraid-SDK is free software released under the GNU General Public License v3
# or later. You can redistribute and/or modify it under the terms of the GPL v3.
# See the LICENSE file in the project root or <https://www.gnu.org/licenses/gpl-3.0.html>.
#
# THERE IS NO WARRANTY for the qBraid-SDK, as per Section 15 of the GPL v3.

"""
Unit tests for remote job submissions to the NEC Vector Annealer using the QbraidProvider.

"""
import pytest
from qbraid_core import QbraidSession

from qbraid import QbraidProvider
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

    job = device.run(qubo, params=params)

    job.wait_for_final_state()

    result = job.result()

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
