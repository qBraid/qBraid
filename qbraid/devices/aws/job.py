# Copyright 2019-2019 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"). You
# may not use this file except in compliance with the License. A copy of
# the License is located at
#
#     http://aws.amazon.com/apache2.0/
#
# or at https://github.com/aws/amazon-braket-sdk-python/blob/main/LICENSE.
# This file is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR
# CONDITIONS OF ANY KIND, either express or implied. See the License for
# the specific language governing permissions and limitations under the License.
#
# NOTICE: This file has been modified from the original:
# https://github.com/aws/amazon-braket-sdk-python/blob/main/src/braket/tasks/quantum_task.py

"""BraketQuantumtaskWrapper Class"""

import asyncio
from typing import Any, Dict, Union

from braket.tasks.quantum_task import QuantumTask
from braket.tasks.annealing_quantum_task_result import AnnealingQuantumTaskResult
from braket.tasks.gate_model_quantum_task_result import GateModelQuantumTaskResult

from qbraid.devices.job import JobLikeWrapper


class BraketQuantumTaskWrapper(JobLikeWrapper):
    """Wrapper class for Amazon Braket ``QuantumTask`` objects.

    Args:
        device: the BraketDeviceWrapper associated with this quantum task i.e. job
        quantum_task (BraketQuantumTask): a braket ``QuantumTask`` object used to run circuits.

    """
    def __init__(self, device, quantum_task: QuantumTask):

        # redundant super delegation but might at more functionality later
        super().__init__(device, quantum_task)
        self.device = device
        self.vendor_jlo = quantum_task

    @property
    def job_id(self):
        """Return a unique id identifying the task."""
        return self.vendor_jlo.id

    def metadata(self, **kwargs) -> Dict[str, Any]:
        """Get task metadata.

        Args:
            **kwargs:
                use_cached_value (bool, optional): If True, uses the value retrieved from the
                    previous request.

        Returns:
            Dict[str, Any]: The metadata regarding the job. If `use_cached_value` is True,
            then the value retrieved from the most recent request is used.

        """
        return self.vendor_jlo.metadata(**kwargs)

    def result(self) -> Union[GateModelQuantumTaskResult, AnnealingQuantumTaskResult]:
        """Return the results of the job."""
        return self.vendor_jlo.result()

    def async_result(self) -> asyncio.Task:
        """asyncio.Task: Get the quantum task result asynchronously."""
        return self.vendor_jlo.async_result()

    def cancel(self):
        """Cancel the quantum task."""
        return self.vendor_jlo.cancel()

    def status(self) -> str:
        """State of the quantum task"""
        return self.vendor_jlo.state()
