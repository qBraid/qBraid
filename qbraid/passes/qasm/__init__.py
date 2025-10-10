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
Module for transforming and extracting data from OpenQASM programs.

.. currentmodule:: qbraid.passes.qasm

Functions
----------

.. autosummary::
   :toctree: ../stubs/

    rebase
    insert_gate_def
    replace_gate_names
    add_stdgates_include
    remove_stdgates_include
    convert_qasm_pi_to_decimal
    normalize_qasm_gate_params

"""
from .compat import (
    add_stdgates_include,
    convert_qasm_pi_to_decimal,
    insert_gate_def,
    normalize_qasm_gate_params,
    remove_stdgates_include,
    replace_gate_names,
)
from .decompose import rebase

__all__ = [
    "rebase",
    "insert_gate_def",
    "replace_gate_names",
    "add_stdgates_include",
    "remove_stdgates_include",
    "convert_qasm_pi_to_decimal",
    "normalize_qasm_gate_params",
]
