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
# https://github.com/aws/amazon-braket-sdk-python/blob/main/src/braket/devices/device.py

"""BraketDeviceWrapper Class"""

from qbraid.devices.aws.job import BraketQuantumTaskWrapper
from qbraid.devices.device import DeviceLikeWrapper
from qbraid.devices._utils import BRAKET_PROVIDERS


class BraketDeviceWrapper(DeviceLikeWrapper):
    """Wrapper class for Amazon Braket ``Device`` objects.

    Args:
        name (str): a Braket supported device
        provider (str): the provider that this device comes from
        fields: Any kwarg options to pass to the backend for running the config. If a key is
            also present in the options attribute/object then the expectation is that the value
            specified will be used instead of what's set in the options object.

    Raises:
        DeviceError: if input field not a valid options

    """
    def __init__(self, name, provider, **fields):

        super().__init__(name, provider, **fields)
        self._vendor = "AWS"
        self.vendor_dlo = self._get_device_obj(BRAKET_PROVIDERS)

    @classmethod
    def _default_options(cls):
        """Return the default options for running this device."""
        return NotImplementedError

    def run(self, run_input, *args, **kwargs):
        """Run a quantum task specification on this quantum device. A task can be a circuit or an
        annealing problem.

        Args:
            run_input (Union[Circuit, Problem]):  Specification of a task to run on device.
            kwargs:
                shots (int): The number of times to run the task on the device.

        Returns:
            BraketJobWrapper: The :class:`~qbraid.devices.braket.job.BraketJobWrapper` job object
                for the run.
            QuantumTask: The QuantumTask tracking task execution on this device

        """
        braket_device = self.vendor_dlo
        braket_quantum_task = braket_device.run(run_input, *args, **kwargs)
        qbraid_job = BraketQuantumTaskWrapper(self, braket_quantum_task)
        return qbraid_job
