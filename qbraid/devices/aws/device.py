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

from typing import TYPE_CHECKING

from braket.aws import AwsDevice
from braket.devices import LocalSimulator
from braket.ocean_plugin import BraketDWaveSampler
from dwave.system.composites import EmbeddingComposite
import dwave_networkx as dnx

from qbraid.devices._utils import get_config
from qbraid.devices.aws.job import BraketQuantumTaskWrapper
from qbraid.devices.device import DeviceLikeWrapper

if TYPE_CHECKING:
    from networkx.classes.graph import Graph as nxGraph


class BraketDeviceWrapper(DeviceLikeWrapper):
    """Wrapper class for Amazon Braket ``Device`` objects."""

    def __init__(self, name, provider, **fields):
        """Create a BraketDeviceWrapper

        Args:
            name (str): a Braket supported device
            provider (str): the provider that this device comes from
            fields: Any kwarg options to pass to the backend for running the config. If a key is
                also present in the options attribute/object then the expectation is that the value
                specified will be used instead of what's set in the options object.

        Raises:
            DeviceError: if input field not a valid options

        """
        super().__init__(name, provider, vendor="AWS", **fields)
        if self.requires_creds:
            bucket = get_config("s3_bucket", "AWS")
            folder = get_config("s3_folder", "AWS")
            self.s3_location = (bucket, folder)

            if provider == "D-Wave":
                dwave_sampler = BraketDWaveSampler(self.s3_location, self._arn)
                self.sampler = EmbeddingComposite(dwave_sampler)
        else:
            self._arn = None
            self.s3_location = None
            self.sampler = None

    def _init_cred_device(self, device_ref):
        """Initialize an AWS credentialed device."""
        if device_ref[0:3] == "arn":
            self._arn = device_ref
            return AwsDevice(device_ref)
        return LocalSimulator(backend=device_ref)

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
        run_input = self._compat_run_input(run_input)
        braket_device = self.vendor_dlo
        if self.requires_creds:
            braket_quantum_task = braket_device.run(run_input, self.s3_location, *args, **kwargs)
        else:
            braket_quantum_task = braket_device.run(run_input, *args, **kwargs)
        qbraid_job = BraketQuantumTaskWrapper(self, braket_quantum_task)
        return qbraid_job

    def min_vertex_cover(self, graph: 'nxGraph', weighted=False, **kwargs):
        """Returns an approximate minimum weighted vertex cover.

        Defines a QUBO with ground states corresponding to a minimum weighted vertex cover and uses
        the BraketDWaveSampler to sample from it. A vertex cover is a set of vertices such that each
        edge of the graph is incident with at least one vertex in the set. A minimum weighted vertex
        cover is the vertex cover of minimum total node weight.

        Args:
            graph (nxGraph): The graph on which to find a minimum vertex cover.
            weighted (optional, bool): if True, calculates the minimum *weighted* vertex cover

        Returns:
            vertex_cover (lst): List of nodes that form a minimum (non/weighted) vertex cover.

        """
        if weighted:
            return dnx.min_weighted_vertex_cover(graph, sampler=self.sampler, **kwargs)
        return dnx.min_vertex_cover(graph, sampler=self.sampler, **kwargs)




