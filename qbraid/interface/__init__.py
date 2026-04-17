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
Module providing utilities for interfacing with supported quantum programs.

.. currentmodule:: qbraid.interface

Functions
-----------

.. autosummary::
   :toctree: ../stubs/

   circuits_allclose
   assert_allclose_up_to_global_phase

"""
from .circuit_equality import assert_allclose_up_to_global_phase, circuits_allclose
from .random import random_circuit, random_unitary_matrix

__all__ = [
    "assert_allclose_up_to_global_phase",
    "circuits_allclose",
    "random_circuit",
    "random_unitary_matrix",
]
