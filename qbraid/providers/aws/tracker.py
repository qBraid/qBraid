# Copyright (C) 2023 qBraid
#
# This file is part of the qBraid-SDK
#
# The qBraid-SDK is free software released under the GNU General Public License v3
# or later. You can redistribute and/or modify it under the terms of the GPL v3.
# See the LICENSE file in the project root or <https://www.gnu.org/licenses/gpl-3.0.html>.
#
# THERE IS NO WARRANTY for the qBraid-SDK, as per Section 15 of the GPL v3.

"""
Module containg Amazon Braket cost tracker helper functions

"""
from decimal import Decimal
from typing import Any, Dict

from braket.aws import AwsDevice, AwsQuantumTask, AwsSession
from braket.tracking.tracker import Tracker, _get_simulator_task_cost
from braket.tracking.tracking_context import register_tracker
from braket.tracking.tracking_events import _TaskCompletionEvent, _TaskCreationEvent


def generate_creation_event(boto_data: Dict[str, Any]) -> _TaskCreationEvent:
    """Generate a task creation event."""
    job_token = boto_data.pop("jobToken", None)
    return _TaskCreationEvent(
        arn=boto_data["quantumTaskArn"],
        shots=boto_data["shots"],
        is_job_task=(job_token is not None),
        device=boto_data["deviceArn"],
    )


def generate_completion_event(boto_data: Dict[str, Any]) -> _TaskCompletionEvent:
    """Generate a task completion event."""
    task_arn = boto_data["quantumTaskArn"]
    result = AwsQuantumTask(task_arn).result()
    execution_duration = None
    try:
        execution_duration = result.additional_metadata.simulatorMetadata.executionDuration
    except AttributeError:
        pass

    completion_data = {
        "arn": task_arn,
        "status": boto_data["status"],
        "execution_duration": execution_duration,
    }
    return _TaskCompletionEvent(**completion_data)


def get_simulator_task_cost(boto_data: Dict[str, Any]) -> Decimal:
    """Calculate the total cost of an Amazon Braket simulator quantum task."""
    tracker = Tracker()
    register_tracker(tracker)
    creation_event = generate_creation_event(boto_data)
    completion_event = generate_completion_event(boto_data)
    tracker.receive_event(creation_event)
    tracker.receive_event(completion_event)

    task_arn = boto_data["quantumTaskArn"]
    details = tracker.quantum_tasks_statistics()
    return _get_simulator_task_cost(task_arn, details)


def get_qpu_task_cost(boto_data: Dict[str, Any]) -> Decimal:
    """Calculate the total cost of an Amazon Braket QPU quantum task."""
    raise NotImplementedError


def get_quantum_task_cost(task_arn: str, aws_session: AwsSession) -> Decimal:
    """Returns the cost of quantum task run on an AWS device

    Args:
        task_arn (str): The quantumTaskArn.
        aws_session (AwsSession): The session associated with account that submitted the task.

    Returns:
        Decimal: The estimated total cost in USD

    Raises:
        ValueError: If the task is not in final state
    """
    braket_client = aws_session.braket_client
    response = braket_client.get_quantum_task(quantumTaskArn=task_arn)
    status = response["status"]

    if status in ["FAILED", "CANCELLED"]:
        return float(0)

    if status != "COMPLETED":
        raise ValueError(f"Task {task_arn} is not COMPLETED. " f"Current state is {status}.")

    device_arn = response["deviceArn"]
    device = AwsDevice(arn=device_arn, aws_session=aws_session)
    device_type = device.type.value

    task_cost = {
        "SIMULATOR": get_simulator_task_cost,
        "QPU": get_qpu_task_cost,
    }

    try:
        return task_cost[device_type](response)
    except KeyError:
        raise ValueError(f"Device type {device_type} is not supported.")
