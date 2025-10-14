# Copyright 2025 qBraid
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
Mdule submiting and managing quantm tasks through AWS
and Amazon Braket supported devices.

.. currentmodule:: qbraid.runtime.aws

Classes
---------

.. autosummary::
   :toctree: ../stubs/

    BraketProvider
    BraketDevice
    BraketQuantumTask

"""
from .device import BraketDevice
from .job import BraketQuantumTask
from .provider import BraketProvider

__all__ = [
    "BraketDevice",
    "BraketProvider",
    "BraketQuantumTask",
]
