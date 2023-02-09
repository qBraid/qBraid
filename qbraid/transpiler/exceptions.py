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
Module defining exceptions for errors raised while handling circuits.

"""

from qbraid.exceptions import QbraidError


class CircuitConversionError(QbraidError):
    """Base class for errors raised while converting a circuit."""


class QasmError(QbraidError):
    """For errors raised while converting circuits to/from QASM."""
