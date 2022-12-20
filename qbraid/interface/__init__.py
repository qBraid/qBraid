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
===============================================
Interface (:mod:`qbraid.interface`)
===============================================

.. currentmodule:: qbraid.interface

.. autosummary::
   :toctree: ../stubs/

   to_unitary
   unitary_to_little_endian
   convert_to_contiguous
   circuits_allclose
   random_circuit
   draw
   ContiguousConversionError
   UnitaryCalculationError

"""
from .calculate_unitary import (
    UnitaryCalculationError,
    circuits_allclose,
    to_unitary,
    unitary_to_little_endian,
)
from .convert_to_contiguous import ContiguousConversionError, convert_to_contiguous
from .draw_circuit import draw
from .programs import random_circuit
