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
This top level module contains the main qBraid public functionality.

.. currentmodule:: qbraid

.. _data_types:

Data Types
-----------

.. autodata:: QPROGRAM
   :annotation: = Type alias defining all supported quantum circuit / program types

Functions
----------

.. autosummary::
   :toctree: ../stubs/

   get_devices
   refresh_devices
   circuit_wrapper
   device_wrapper
   job_wrapper
   get_jobs

Exceptions
-----------

.. autosummary::
   :toctree: ../stubs/

   QbraidError
   PackageValueError
   ProgramTypeError

"""
from . import _warnings
from ._qprogram import QPROGRAM, QPROGRAM_LIBS, QPROGRAM_TYPES
from ._version import __version__
from .exceptions import PackageValueError, ProgramTypeError, QbraidError
from .get_devices import get_devices, refresh_devices
from .get_jobs import get_jobs
from .wrappers import circuit_wrapper, device_wrapper, job_wrapper
