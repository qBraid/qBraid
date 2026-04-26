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
Module submitting and managing quantum tasks through AWS
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

__all__ = [
    "BraketDevice",
    "BraketProvider",
    "BraketQuantumTask",
]


def __getattr__(name):
    if name == "BraketProvider":
        from .provider import BraketProvider

        return BraketProvider
    if name == "BraketDevice":
        from .device import BraketDevice

        return BraketDevice
    if name == "BraketQuantumTask":
        from .job import BraketQuantumTask

        return BraketQuantumTask
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
