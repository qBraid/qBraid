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
Module defining BraketLocalSimulatorWrapper Class

"""
from typing import TYPE_CHECKING

from braket.devices import LocalSimulator

from qbraid.devices.device import DeviceLikeWrapper
from qbraid.devices.enums import DeviceStatus
from qbraid.devices.exceptions import DeviceError

from .localjob import BraketLocalQuantumTaskWrapper

if TYPE_CHECKING:
    import braket

    import qbraid


class BraketLocalSimulatorWrapper(DeviceLikeWrapper):
    """Wrapper class for Amazon Braket ``LocalSimulator`` objects."""

    def _get_device(self):
        """Initialize an AWS local simulator."""
        try:
            return LocalSimulator(backend=self._obj_arg)
        except ValueError as err:
            raise DeviceError("Device not found.") from err

    def _vendor_compat_run_input(self, run_input):
        return run_input

    @property
    def status(self) -> "qbraid.devices.DeviceStatus":
        """Return the status of this Device.

        Returns:
            The status of this Device
        """
        return DeviceStatus.ONLINE

    def run(
        self, run_input: "braket.circuits.Circuit", *args, **kwargs
    ) -> "qbraid.devices.aws.BraketLocalQuantumTaskWrapper":
        """Run a quantum task specification on this quantum device. A task can be a circuit or an
        annealing problem.

        Args:
            run_input: Specification of a task to run on device.

        Keyword Args:
            shots (int): The number of times to run the task on the device. Default is ``0``.

        Returns:
            The job like object for the run.

        """
        run_input, _ = self._compat_run_input(run_input)
        local_quantum_task = self.vendor_dlo.run(run_input, *args, **kwargs)
        return BraketLocalQuantumTaskWrapper(self, local_quantum_task)
