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
Exceptions raised by the Quantinuum runtime provider.

Defined in their own module so they carry a public, importable path in
tracebacks and docs, and so ``_transport`` can use them without a circular
import through ``device``.

"""
from qbraid.runtime.exceptions import QbraidRuntimeError


class QuantinuumDeviceError(QbraidRuntimeError):
    """Exception raised by QuantinuumDevice."""


class QuantinuumJobError(QbraidRuntimeError):
    """Class for errors raised while processing a Quantinuum job."""
