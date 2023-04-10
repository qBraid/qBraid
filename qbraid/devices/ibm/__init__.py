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
IBM Devices Interface (:mod:`qbraid.devices.ibm`)
==================================================

.. currentmodule:: qbraid.devices.ibm

This module contains the classes used to run quantum circuits on devices available through IBM.

.. autosummary::
   :toctree: ../stubs/

   ibm_provider
   ibmq_least_busy_qpu
   QiskitBackendWrapper
   QiskitBasicAerWrapper
   QiskitJobWrapper
   QiskitBasicAerJobWrapper
   QiskitResultWrapper

"""
from .result import QiskitResultWrapper
from .device import QiskitBackendWrapper
from .job import QiskitJobWrapper
from .localdevice import QiskitBasicAerWrapper
from .localjob import QiskitBasicAerJobWrapper
from .provider import ibm_provider, ibmq_least_busy_qpu
