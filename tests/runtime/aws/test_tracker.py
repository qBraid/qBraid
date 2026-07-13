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
Unit tests for the Amazon Braket cost tracker interface.

"""
from unittest.mock import patch

from braket.tracking.tracking_context import active_trackers
from braket.tracking.tracking_events import _TaskCompletionEvent

from qbraid.runtime.aws.tracker import _get_tracker_task_details


def test_get_tracker_task_details_does_not_leak_tracker():
    """_get_tracker_task_details must deregister its Tracker from Braket's
    process-global tracking context.

    Leaking a tracker on every cost lookup makes ``broadcast_event`` iterate an
    ever-growing, lock-free set, widening a thread-safety window where a
    concurrent ``get_quantum_task`` raises "Set changed size during iteration".
    """
    boto_data = {
        "quantumTaskArn": "arn:aws:braket:us-east-1:123456789012:quantum-task/abc",
        "shots": 100,
        "deviceArn": "arn:aws:braket:::device/quantum-simulator/amazon/sv1",
        "status": "COMPLETED",
    }
    completion = _TaskCompletionEvent(
        arn=boto_data["quantumTaskArn"], status="COMPLETED", execution_duration=None
    )

    trackers_before = len(active_trackers())
    # Patch out the completion event to avoid a live AwsQuantumTask.result() call.
    with patch("qbraid.runtime.aws.tracker._generate_completion_event", return_value=completion):
        details = _get_tracker_task_details(dict(boto_data))

    assert details["shots"] == 100
    # No tracker leaked: the active set returns to its pre-call size.
    assert len(active_trackers()) == trackers_before
