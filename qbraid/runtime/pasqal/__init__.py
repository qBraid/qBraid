# Copyright 2026 qBraid
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
Module for submitting and managing jobs through the Pasqal Cloud Services API.

.. currentmodule:: qbraid.runtime.pasqal

Classes
--------

.. autosummary::
   :toctree: ../stubs/

    PasqalProvider
    PasqalDevice
    PasqalJob

"""

from .device import PasqalDevice
from .job import PasqalJob
from .provider import PasqalProvider

__all__ = ["PasqalDevice", "PasqalJob", "PasqalProvider"]
