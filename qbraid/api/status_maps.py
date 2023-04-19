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
Module to map qbraid status to equivalent status of each
supported front-end.

"""
from qbraid.devices.enums import JobStatus

AwsQuantumTask = {
    "CREATED": JobStatus.INITIALIZING,
    "QUEUED": JobStatus.QUEUED,
    "RUNNING": JobStatus.RUNNING,
    "CANCELLING": JobStatus.CANCELLING,
    "CANCELLED": JobStatus.CANCELLED,
    "COMPLETED": JobStatus.COMPLETED,
    "FAILED": JobStatus.FAILED,
}

IBMJob = {
    "JobStatus.INITIALIZING": JobStatus.INITIALIZING,
    "JobStatus.QUEUED": JobStatus.QUEUED,
    "JobStatus.VALIDATING": JobStatus.VALIDATING,
    "JobStatus.RUNNING": JobStatus.RUNNING,
    "JobStatus.CANCELLED": JobStatus.CANCELLED,
    "JobStatus.DONE": JobStatus.COMPLETED,
    "JobStatus.ERROR": JobStatus.FAILED,
}

STATUS_MAP = {"AWS": AwsQuantumTask, "IBM": IBMJob}
