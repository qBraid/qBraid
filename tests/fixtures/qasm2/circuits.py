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
Module containing qasm programs used for testing

"""
import os

QASMType = str
current_dir = os.path.dirname(os.path.abspath(__file__))


def _read_qasm_file(filename: str) -> QASMType:
    """Reads a qasm file from the qasm_lib directory"""
    return open(os.path.join(current_dir, filename), mode="r", encoding="utf-8").read()


def qasm2_bell() -> QASMType:
    """Returns OpenQASM2 bell circuit"""
    return _read_qasm_file("bell.qasm")


def qasm2_shared15() -> QASMType:
    """Returns OpenQASM2 15 gate test circuit."""
    return _read_qasm_file("shared15.qasm")


def qasm2_cirq_shared15() -> QASMType:
    """Returns OpenQASM 2 15 gate test circuit with no gate defs."""
    return _read_qasm_file("shared15_cirq.qasm")
