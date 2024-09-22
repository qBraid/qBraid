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
Module for interfacing with the Amazon Braket cost tracker

"""
from decimal import Decimal
from typing import Any, Optional

from boto3.session import Session
from braket.aws import AwsDevice, AwsQuantumTask, AwsSession
from braket.tracking.tracker import Tracker, _get_qpu_task_cost, _get_simulator_task_cost
from braket.tracking.tracking_context import register_tracker
from braket.tracking.tracking_events import _TaskCompletionEvent, _TaskCreationEvent


def _generate_creation_event(boto_data: dict[str, Any]) -> _TaskCreationEvent:
    """Generate a task creation event."""
    job_token = boto_data.pop("jobToken", None)
    return _TaskCreationEvent(
        arn=boto_data["quantumTaskArn"],
        shots=boto_data["shots"],
        is_job_task=(job_token is not None),
        device=boto_data["deviceArn"],
    )


def _generate_completion_event(
    boto_data: dict[str, Any], aws_session: Optional[AwsSession] = None
) -> _TaskCompletionEvent:
    """Generate a task completion event."""
    task_arn = boto_data["quantumTaskArn"]
    result = AwsQuantumTask(task_arn, aws_session=aws_session).result()
    execution_duration = None
    try:
        execution_duration = result.additional_metadata.simulatorMetadata.executionDuration
    except AttributeError:  # pragma: no cover
        pass

    completion_data = {
        "arn": task_arn,
        "status": boto_data["status"],
        "execution_duration": execution_duration,
    }
    return _TaskCompletionEvent(**completion_data)


def _get_tracker_task_details(
    boto_data: dict[str, Any], aws_session: Optional[AwsSession] = None
) -> dict[str, Any]:
    """Get the quantum task details populated by the Amazon Braket cost tracker."""
    tracker = Tracker()
    register_tracker(tracker)
    creation_event = _generate_creation_event(boto_data)
    completion_event = _generate_completion_event(boto_data, aws_session=aws_session)
    tracker.receive_event(creation_event)
    tracker.receive_event(completion_event)

    task_arn = boto_data["quantumTaskArn"]
    return tracker._resources[task_arn]


def get_quantum_task_cost(task_arn: str, aws_session: Optional[AwsSession] = None) -> Decimal:
    """Returns the cost of quantum task run on an AWS device

    Args:
        task_arn (str): The quantumTaskArn.
        aws_session (optional, braket.aws.AwsSession): Session with which to retrieve the task

    Returns:
        decimal.Decimal: The estimated total cost in USD

    Raises:
        ValueError: If quantum task not found or not in final state, or device type not supported.
    """
    task_region = task_arn.split(":")[3]

    if aws_session is None:
        boto_session = Session(region_name=task_region)
        aws_session = AwsSession(boto_session=boto_session)

    elif aws_session.region != task_region:
        raise ValueError(
            f"AwsSession region {aws_session.region} does not match task region {task_region}"
        )

    braket_client = aws_session.braket_client
    response = braket_client.get_quantum_task(quantumTaskArn=task_arn)
    status = response["status"]

    if status in ["FAILED", "CANCELLED"]:
        return Decimal(0)

    if status != "COMPLETED":
        raise ValueError(f"Task {task_arn} is not COMPLETED. Current state is {status}.")

    device_arn = response["deviceArn"]
    device = AwsDevice(arn=device_arn, aws_session=aws_session)
    device_type = device.type.value

    task_cost = {
        "SIMULATOR": _get_simulator_task_cost,
        "QPU": _get_qpu_task_cost,
    }

    details = _get_tracker_task_details(response, aws_session=aws_session)

    try:
        return task_cost[device_type](task_arn, details)
    except KeyError as err:
        raise ValueError(f"Device type {device_type} is not supported.") from err
