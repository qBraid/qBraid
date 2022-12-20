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
Module defining BraketQuantumtaskWrapper Class

"""
from typing import TYPE_CHECKING

from qbraid.devices.localjob import LocalJobWrapper

from .result import BraketResultWrapper

if TYPE_CHECKING:
    import qbraid


class BraketLocalQuantumTaskWrapper(LocalJobWrapper):
    """Wrapper class for Amazon Braket ``LocalQuantumTask`` objects."""

    @property
    def id(self) -> str:
        """Return a unique id identifying the job."""
        return self.vendor_jlo.id

    def metadata(self) -> dict:
        """Return the metadata regarding the job."""
        return dict(self.vendor_jlo.result().task_metadata)

    def result(self) -> "qbraid.devices.aws.BraketResultWrapper":
        """Return the results of the job."""
        return BraketResultWrapper(self.vendor_jlo.result())
