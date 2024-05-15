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
Fixtures imported/defined in this file can be used by any test in this directory
without needing to import them (pytest will automatically discover them).

"""
import braket.circuits
import numpy as np
import pytest

from qbraid.runtime.braket import BraketProvider


@pytest.fixture
def braket_most_busy():
    """Return the most busy device for testing purposes."""
    provider = BraketProvider()
    qbraid_devices = provider.get_devices(
        types=["QPU"], statuses=["ONLINE"], provider_names=["Rigetti", "IonQ", "Oxford"]
    )

    qbraid_device = None
    max_queued = 0
    for device in qbraid_devices:
        jobs_queued = device.queue_depth()
        if jobs_queued is not None and jobs_queued > max_queued:
            max_queued = jobs_queued
            qbraid_device = device
    yield qbraid_device


@pytest.fixture
def aws_session():
    """Return AWS session."""
    provider = BraketProvider()
    yield provider._get_aws_session()


@pytest.fixture
def braket_circuit():
    """Low-depth, one-qubit Braket circuit to be used for testing."""
    circuit = braket.circuits.Circuit()
    circuit.h(0)
    circuit.ry(0, np.pi / 2)
    yield circuit


@pytest.fixture
def braket_provider():
    """Return a BraketProvider instance."""
    yield BraketProvider()
