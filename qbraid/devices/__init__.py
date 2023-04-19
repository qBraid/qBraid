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
====================================
 Devices (:mod:`qbraid.devices`)
====================================

.. currentmodule:: qbraid.devices

Devices API
------------

.. autosummary::
   :toctree: ../stubs/

   DeviceError
   DeviceLikeWrapper
   DeviceStatus
   DeviceType
   JobError
   JobLikeWrapper
   JobStatus
   ResultWrapper
   is_status_final


"""
from .device import DeviceLikeWrapper
from .enums import DeviceStatus, DeviceType, JobStatus, is_status_final
from .exceptions import DeviceError, JobError
from .job import JobLikeWrapper
from .result import ResultWrapper
