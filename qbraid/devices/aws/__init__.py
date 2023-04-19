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

# isort: skip_file
# pylint: skip-file

"""
==================================================
AWS Devices Interface (:mod:`qbraid.devices.aws`)
==================================================

.. currentmodule:: qbraid.devices.aws

This module contains the classes used to run quantum circuits on devices available through AWS.

.. autosummary::
   :toctree: ../stubs/

   AwsDeviceWrapper
   AwsQuantumTaskWrapper
   AwsGateModelResultWrapper

"""
from .result import AwsGateModelResultWrapper
from .device import AwsDeviceWrapper
from .job import AwsQuantumTaskWrapper
