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
Module defining exceptions for errors raised by qBraid.

"""

from ._qprogram import QPROGRAM_LIBS


class QbraidError(Exception):
    """Base class for errors raised by qBraid."""


class PackageValueError(QbraidError):
    """Class for errors raised due to unsupported quantum frontend package"""

    def __init__(self, package):
        msg = (
            f"Quantum frontend module {package} is not supported.\n"
            f"Frontends supported by qBraid are: {QPROGRAM_LIBS}"
        )
        super().__init__(msg)


class ProgramTypeError(QbraidError):
    """Class for errors raised when processing unsupported quantum programs"""

    def __init__(self, program):
        msg = f"Quantum program of type {type(program)} is not supported."
        super().__init__(msg)
